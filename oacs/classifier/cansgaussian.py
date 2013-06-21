#!/usr/bin/env python
# encoding: utf-8

## @package cansgaussian
#
# CANS (Cluster Augmented Negative Selection Algorithm or Cluster Augmented Naive Bayes)

from oacs.classifier.univariategaussian import UnivariateGaussian
from oacs.classifier.multivariategaussian import MultivariateGaussian

import math
import numbers
import numpy as np
import pandas as pd
from numpy import pi, exp, log
from scipy.stats import scoreatpercentile

## CANSGaussian
#
# CANS (Cluster Augmented Negative Selection Algorithm or Cluster Augmented Naive Bayes) is an AIS (Artificial Immune System) classifier class, which is a mix between UnivariateGaussian and MultivariateGaussian: highly correlated features (using Mutual Information) will be clustered and MultivariateGaussian will be used on them, and then a UnivariateGaussian will be performed on all the clusters (which may include only one feature or several correlated features)
class CANSGaussian(MultivariateGaussian, UnivariateGaussian):

    ## @var config
    # An instance of the ConfigParser object, already loaded

    ## Constructor
    # @param config An instance of the ConfigParser class
    def __init__(self, config=None, *args, **kwargs):
        return MultivariateGaussian.__init__(self, config, *args, **kwargs)

    ## Learn the parameters from a given set X of examples, and labels Y
    # @param X Samples set
    # @param Y Labels set (corresponding to X)
    def learn(self, X=None, Y=None, *args, **kwargs):

        weights = 'framerepeat'

        # == Preparing the samples set
        Yt = Y[Y==0].dropna() # get the list of non-anomalous examples
        Xt = X.iloc[Yt.index] # filter out anomalous examples and keep only non-anomalous ones


        # == Computing the Mutual Information matrix (degree of correlation between each two features)
        # Compute the required stats
        Mu = self.mean(X, X[weights]) # Mean
        Var = self.variance(X, Mu, X[weights]) # Vector of variances
        #Covar = self.covar(X, Mu, 'framerepeat') # Covariance matrix
        H = CANSGaussian.entropy(X, Var) # Entropy of each single variable (given its gaussian distribution)
        #H2 = CANSGaussian.entropypairwise_alt(X, Covar) # Joint entropy of each pair of two variables
        H2 = CANSGaussian.entropypairwise(X, Mu, weights) # Joint entropy of each pair of two variables

        # Compute the Mutual Information matrix
        MI = CANSGaussian.mutualinformation(X, H, H2)

        # Compute the clusters
        clusters = CANSGaussian.micluster(X, MI, cmax=self.config.get("cansgaussian_maxitemspercluster", 1), mergeclusters=self.config.get("cansgaussian_mergeclusters", False), MImax=self.config.get("cansgaussian_scorethreshold", None))

        # Computing the covariance matrixes for each subset of clusters
        Covar = []
        for cind, cluster in enumerate(clusters):
            # Compute only if there is more than one feature in the cluster (else we will just use a UnivariateGaussian on this feature, thus we don't need the covariance matrix)
            if (len(cluster) > 1):
                Covar.insert(cind, MultivariateGaussian.covar(X.ix[:, cluster], Mu[cluster], weights))

        return {'Mu': Mu, 'Var': Var, 'Covar': Covar, 'H': H, 'H2': H2, 'MI': MI, 'Clusters': clusters} # always return a dict of variables if you want your variables saved durably and accessible later

    ## Multivariate gaussian prediction of the probability/class of an example given a set of parameters (weighted mean and covariance matrix)
    # @param X One unknown example to label
    # @param Mu Weighted mean of X
    # @param Sigma2 Covariance matrix of X
    # TODO: compatibility with more than one sample (detect type==pdSseries)?
    def predict(self, X=None, Clusters=None, Mu=None, Var=None, Covar=None, *args, **kwargs):
        if 'framerepeat' in X:
            X = X.drop(['framerepeat'])
        if 'framerepeat' in Mu:
            Mu = Mu.drop(['framerepeat'])
        if 'framerepeat' in Var:
            Var = Var.drop(['framerepeat'])
        # there cannot be the framerepeat column in the Covar list since it's taken care of at the learning process

        Pred = pd.Series() # Creating an empty vector
        for i, cluster in enumerate(Clusters):
            # Cluster contains several features, we compute the multivariate gaussian
            if len(cluster) > 1:
                dictofvars = MultivariateGaussian._predict(X[cluster], Mu[cluster], Covar[i])
                Pred = Pred.set_value("C%i" % i, dictofvars['Prediction'] )
            # Else there is only a single feature in this cluster, we just compute the univariate gaussian
            elif len(cluster) == 1:
                feature = cluster[0]
                dictofvars = UnivariateGaussian._predict(X[feature], Mu[feature], Var[feature])
                Pred = Pred.set_value("C%i" % i, dictofvars['Prediction'] )

        # Compute the product of all probabilities (p1 = proba of feature 1 being normal; p1*p2*p3*...*pn)
        if not isinstance(Pred, numbers.Number):
            Pred = Pred.prod()

        return {'Prediction': Pred} # return the class of the sample(s)

    ## Compute the weighted mean of the dataset
    # @param X Samples dataset
    # @param weights Vector/Series of weights (ie: number of times one sample has to be repeated) - default: X['framerepeat']
    def mean(self, X, weights=None):
        return UnivariateGaussian.mean(X, weights)

    ## Compute the weighted unbiased variance of each feature for a given dataset
    # @param X Samples dataset
    # @param mean Weighted mean
    # @param weights Vector/Series of weights (ie: number of times one sample has to be repeated) - default: X['framerepeat']
    def variance(self, X, mean, weights=None):
        return UnivariateGaussian.variance(X, mean, weights)

    ## Compute the weighted covariance matrix of the dataset
    # Alternative to pandas.DataFrame.cov(), because pandas's and numpy's cov() can't account for weights (if you set mean = X.mean() and weights = None, then you'll get the exact same result as X.cov())
    # @param X One example or a dataset of examples (must have the same columns/keys as mean)
    # @param mean Weighted mean (must have the same columns/keys as X, else you will get a weird result, because pandas will still try to adapt and things will get really messed up!)
    # @param weights Name of the weights column to remove from the final result (else it may flaw the computation of the prediction)
    def covar(self, X, mean, weights=None):
        return MultivariateGaussian.covar(X, mean, weights)

    ## Compute the differential entropy vector for all features in X (entropy of one single variable, and differential = for continuous distributions)
    # Note: if you used WeightedNormalization before computing the entropy, the entropy will always be the same number for all features. This is normal (I guess! at least it's logical since the variance is normalized).
    # @param X One example or a dataset of examples, only used to get the keys/indexes names (you can pass Var if Var contains the same keys as X)
    # @param Var Vector of variances of each feature in X
    @staticmethod
    def entropy(X, Var):
        # Create an empty vector (filled with NaN)
        H = pd.Series(index=X.columns)
        # For each feature (random variable)
        for index in H.index:
            # can use any base for the log here, the result will still be proportional thus we don't care the base
            # +1 is because log(e) = 1
            H[index] = 0.5 * (log(2*pi*Var[index]) + 1)
        return H

    ## Compute a two-by-two differential joint entropy matrix (a cell contains the value of the entropy between two variables)
    # @param X One example or a dataset of examples (must have the same columns/keys as mean)
    # @param mean Weighted mean (must have the same columns/keys as X, else you will get a weird result, because pandas will still try to adapt and things will get really messed up!)
    # @param weights Name of the weights column to remove from the final result (else it may flaw the computation of the prediction)
    @staticmethod
    def entropypairwise(X, mean, weights=None):
        # Create an empty DataFrame (filled with NaN)
        H2 = pd.DataFrame(index=X.columns, columns=X.columns)
        k = 2 # 2 dimensions here because we have 2 variables. If more, you can raise k
        for index in H2.index:
            for column in H2.index:
                # Diagonal is null: if it's the same index and column, no need to compute: a variable can't bring more information about itself
                if (index == column):
                    H2.ix[index, column] = 0 # actually, computing the entropy would give the same result, but it's more computationally efficient to just set 0 here
                # By symetry, it's useless to recompute the lower part of the entropy matrix
                elif (not math.isnan(H2.ix[column, index]) and H2.ix[column, index]):
                    H2.ix[index, column] = H2.ix[column, index]
                # Compute the entropy by computing the log of the determinant of the covariance matrix
                else:
                    # Compute the covariance of only the two variables (complexity O(2^2 * m) instead of O(m^2) if we computed the whole covariance matrix)
                    # Note: Computing the covariance of two variables is the same as computing the covariance of all variables and then slicing only the columns and indexes for those two variables
                    # Note2: this is equivalent only in terms of value, not in terms of computation efficiency (computing the covariance of two variables is of course a lot quicker)
                    # TODO: make the computation a bit quicker by precomputing: constant = log((2*pi*exp)^k) and then H2... = 0.5 * (constant + log(determinant))
                    Covar = MultivariateGaussian.covar(X.ix[:,[index, column]], mean[[index, column]], weights)
                    # Compute the joint entropy
                    H2.ix[index, column] = 0.5 * log((2*pi*exp(1))**k * np.linalg.det(Covar.ix[[index, column],[index, column]]))

        return H2

    ## Compute a two-by-two differential joint entropy matrix (a cell contains the value of the entropy between two variables)
    # @param X One example or a dataset of examples, only used to get the keys/indexes names (you can pass Covar if Covar contains the same keys as X)
    # @param Covar Covariance matrix
    @staticmethod
    def entropypairwise_alt(X, Covar):
        # Create an empty DataFrame (filled with NaN)
        H2 = pd.DataFrame(index=X.columns, columns=X.columns)
        k = 2 # 2 dimensions here because we have 2 variables. If more, you can raise k
        for index in H2.index:
            for column in H2.index:
                # Diagonal is null: if it's the same index and column, no need to compute: a variable can't bring more information about itself
                if (index == column):
                    H2.ix[index, column] = 0 # actually, computing the entropy would give the same result, but it's more computationally efficient to just set 0 here
                # By symetry, it's useless to recompute the lower part of the entropy matrix
                elif (not math.isnan(H2.ix[column, index]) and H2.ix[column, index]):
                    H2.ix[index, column] = H2.ix[column, index]
                # Compute the entropy by computing the log of the determinant of the covariance matrix
                else:
                    # Note: Computing the covariance of two variables is the same as computing the covariance of all variables and then slicing only the columns and indexes for those two variables
                    # Note2: this is equivalent only in terms of value, not in terms of computation efficiency (computing the covariance of two variables is of course a lot quicker)
                    # TODO: make the computation a bit quicker by precomputing: constant = log((2*pi*exp)^k) and then H2... = 0.5 * (constant + log(determinant))
                    H2.ix[index, column] = 0.5 * log((2*pi*exp(1))**k * np.linalg.det(Covar.ix[[index, column],[index, column]]))

        return H2

    ## Compute the pairwise mutual information matrix for all features
    # Note: Kullback-Leibler divergence is a generalization of Mutual Information, thus this can also be seen as a KL divergence measurement.
    # @param X One example or a dataset of examples, only used to get the keys/indexes names (you can pass H if H contains the same keys as X)
    # @param H Entropy vector for each single variable
    # @param H2 Pairwise entropy matrix, containing the entropy between each couple of variables
    @staticmethod
    def mutualinformation(X, H, H2):
        # Create an empty DataFrame (filled with NaN)
        MI = pd.DataFrame(index=X.columns, columns=X.columns)

        # For each two features (two random variables)
        for index in MI.index:
            for column in MI.columns:
                # Diagonal is null: if it's the same index and column, no need to compute: a variable can't bring more information about itself
                if (index == column):
                    MI.ix[index, column] = H[index] # MI[X|X] = entropy of X
                # By symetry, it's useless to recompute the lower part of the mutual information matrix
                elif (not math.isnan(MI.ix[column, index]) and MI.ix[column, index]):
                    MI.ix[index, column] = MI.ix[column, index]
                # Else we compute the MI
                else:
                    # I(X;X) >= I(X;Y) (which means that any variable Y can only provide as much info about another var X as X can provide about itself), and I(X;X) = H(X), thus by doing H(X) + H(Y) - H(X;Y) the intuition is that we compute the maximum information one can have about X and Y (we know perfectly well X and Y) and we remove the mutual/joint entropy between X and Y (the entropy of both variables at once if they were happening simultaneously). And we know that H(X;Y) <= H(X) + H(Y)
                    MI.ix[index, column] = H[index] + H[column] - H2.ix[index, column]

        return MI

    ## Compute the clustering of features given a Mutual Information matrix
    # @param X One example or a dataset of examples, only used to get the keys/indexes names (you can pass MI if MI contains the same keys as X)
    # @param MI Mutual Information matrix
    # @param cmax Maximum number of features per cluster (cmax=1 means that there's no limit)
    # @param mergeclusters Merge back the clusters together if features correlates whenever possible?
    # @param MImax Keep only MI scores above this threshold (MImax="mean" will use the mean; MImax=[0..1] a float number between 0 and 1 will compute the percentile and drop below this percentile, Mimax=0.5 being the median; MImax=None means no threshold and no MI score dropped)
    @staticmethod
    def micluster(X, MI, cmax=1, mergeclusters=False, MImax=None):

        #== Preparing the Mutual Information data
        # We preprocess the Mutual Information matrix into a sorted vector in descending order of MI score (from the best to the lowest). Each entry will have two keys associated: feature1 and feature2 being the respective names of the features (previously rows and columns).

        # Make sure data is float (number) and not object or string, and drop framerepeat column and row
        MI = MI.astype('float64').drop(['framerepeat'], 1).drop(['framerepeat'], 0)

        # Unstack the Mutual Information matrix into a vector/Serie
        MI = MI.unstack().copy() # Each entry will have two keys associated: feature1 and feature2 being the respective names of the features (previously rows and columns).
        # Sort by MI score
        MI.sort(kind='mergesort')
        # Drop undefined scores
        MI = MI.dropna()
        # Reorder in descending order (because pandas's sort cannot yet sort in descending order, it always sort in ascending order)
        MI = MI.ix[::-1]

        # MImax CUT: if MImax is defined, we drop all scores below this threshold
        # Cut by mean: all values below the mean of scores are dropped
        if (MImax is not None and isinstance(MImax, basestring) and MImax == 'mean'):
            # Compute the mean and set all scores below as NaN
            MI[MI < MI.mean()] = float('NaN')
            # Drop these scores
            MI = MI.dropna()
        # Cut by percentile: compute the specified percentile and drop all scores below this threshold (percentile=0.5=median)
        elif (MImax is not None and 0 <= MImax*100 <= 100):
            # Compute the percentile and set all scores below as Nan
            MI[MI < scoreatpercentile(MI, MImax*100)] = float('NaN')
            # Drop these scores
            MI = MI.dropna()

        #== Clustering the features two-by-two
        clusters = [] # list of sublists, each sublists containing a set of features names that are bound together in the same cluster
        assignments = pd.Series(index=X.columns) # vector of assignments to keep track of which feature is assigned to which cluster
        assignments = assignments.fillna(-1).drop('framerepeat') # initialize the vector with -1 and delete framerepeat (we don't want to bind it nor correlate it to other features)
        curind = 0 # Keep track of the current cluster index (because we want to keep track in the assignments vector)

        #-- First pass: Kruskal-like assignment algorithm
        # We loop through all values of mutual informations and try to cluster together the variables which are the most correlated
        for index in MI.index:
            feature1 = index[0]
            feature2 = index[1]
            # If the two labels are the same, we skip
            if (feature1 == feature2): continue
            # Both feature1 and feature2 are free (not bound to any cluster yet), and they have maximum correlation (at least better than the other choices or either previous choices were not possible because of CMAX CUT), then we bound them together in a new cluster
            if (assignments[feature1] == -1 and assignments[feature2] == -1):
                # Insert both features in a new cluster
                clusters.insert(curind, [feature1, feature2])
                # Update the assignments table to keep track of where are assigned each feature
                assignments[feature1] = curind
                assignments[feature2] = curind
                # Increment the cluster index counter
                curind += 1
            # Feature1 is bound in a cluster but feature2 is free, we try to bind feature2 in the same cluster as feature1
            elif (assignments[feature1] != -1 and assignments[feature2] == -1):
                # Get the index of the cluster where the bound feature is assigned
                ind = int(assignments[feature1]) # convert from numpy types into standard python int type, necessary to be used as a list index
                # CMAX Cut: if we specified a number of items per cluster (cmax > 1) and this cluster already contains the maximum number of items, we skip
                if (cmax > 1 and len(clusters[ind]) >= cmax): continue
                # Add feature2 into the same cluster as feature1
                clusters[ind].append(feature2)
                # Update the assignments table
                assignments[feature2] = ind
            # Same as the previous condition but the other way around (feature2 is bound and feature1 is free)
            elif (assignments[feature1] == -1 and assignments[feature2] != -1):
                # Get the index of the cluster where the bound feature is assigned
                ind = int(assignments[feature2]) # convert from numpy types into standard python int type, necessary to be used as a list index
                # CMAX Cut: if we specified a number of items per cluster (cmax > 1) and this cluster already contains the maximum number of items, we skip
                if (cmax > 1 and len(clusters[ind]) >= cmax): continue
                # Add feature1 into the same cluster as feature2
                clusters[ind].append(feature1)
                # Update the assignments table
                assignments[feature1] = ind
            # Else, both features are already bound in a cluster, then we can't do anything OR we may recluster back together
            elif (assignments[feature1] != -1 and assignments[feature2] != -1):
                # Merge clusters back if possible and if the option is enabled
                if (mergeclusters):
                    ind1 = int(assignments[feature1])
                    ind2 = int(assignments[feature2])
                    # Merge clusters if possible (if both features belong to different clusters)
                    if (ind1 != ind2):
                        # if CMAX CUT doesn't prevent us from merging the clusters because that would merge too many items together
                        if (cmax > 1 and (len(clusters[ind1]) + len(clusters[ind2]) > cmax)): continue
                        # Else we merge the clusters together
                        clusters[ind1].extend(clusters[ind2]) # merge both clusters together in the first one
                        # Re-assigning the variables from cluster2 to cluster1
                        for item in clusters[ind2]:
                            assignments[item] = ind1
                        # Delete the second cluster
                        del clusters[ind2]
                # Else we don't want to recluster thus we just skip here
                else:
                    pass

        #-- Second pass: remaining unassigned variables/features get assigned to their own cluster
        # For each remaining unassigned variable, we simply create a new cluster containing only this variable
        for index in assignments.index:
            if (assignments[index] == -1):
                clusters.insert(curind, [index])
                assignments[index] = curind
                curind += 1

        return clusters

    ## A simple function to print in neat tables the features given a list of clusters
    # @param clusters A list of clusters for the features
    def printclusters(self, clusters):
        inc = 0
        for tab in clusters:
            inc += 1
            print("Tableau %s" % inc)
            for item in tab:
                print(' '*5+"%s" % item)
            print("")
