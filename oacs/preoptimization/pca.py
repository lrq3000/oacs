#!/usr/bin/env python
# encoding: utf-8

## @package PCA
#
# Reduce the dimensionality of the dataset X by using Principal Component Analysis

from oacs.preoptimization.basepreoptimization import BasePreOptimization
from oacs.classifier.univariategaussian import UnivariateGaussian
from oacs.classifier.multivariategaussian import MultivariateGaussian
import pandas as pd
import numpy as np

## PCA
#
# Reduce the dimensionality of the dataset X by using Principal Component Analysis
class PCA(BasePreOptimization):

    ## @var config
    # An instance of the ConfigParser object, already loaded

    ## Constructor
    # @param config An instance of the ConfigParser class
    def __init__(self, config=None, *args, **kwargs):
        return BasePreOptimization.__init__(self, config, *args, **kwargs)

    ## Reduce the dimensionality of the dataset X by using Principal Component Analysis
    # @param X Samples set
    # @param PCA_K At detection, you can reload the previously learnt parameter here
    # @param PCA_U At detection, you can reload the previously learnt parameter here
    # @param PCA_S At detection, you can reload the previously learnt parameter here
    # @param PCA_Threshold Maximum Variation Loss tolerated (between 0 and 1, 1 being 100%). At learning, can be used to find the best PCA_K. Default = 0.01 (= 1% tolerated)
    # @param Sigma2 Reuse an already computed covariance matrix if possible
    # @param Mu Reuse an already computed mean if possible
    def optimize(self, X=None, PCA_K=None, PCA_U=None, PCA_S=None, PCA_Threshold=None, Sigma2=None, Mu=None, *args, **kwargs):

        # DEPRECATED: we don't want to drop anomalous examples here, because we want to keep the eigenvectors where there are a maximum of variances to derive correlations, and anomalous examples can help us gather more variations!
        # Preparing the features: dropping examples labelled as anomalous, else it will fling out the stats
        #Yt = Y[Y==0].dropna() # get the list of non-anomalous examples. WARNING: the dropna() here is VERY necessary, else you will get a batch of True/False boolean values, but you still get all the rows! To trim out the rows we don't won't (Y!=0), we need to use dropna()
        #Xt = X.iloc[Yt.index] # filter out anomalous examples and keep only non-anomalous ones

        # If the parameters were already learned previously, then OK we reuse them. Else we have to compute them.
        if Sigma2 is None or len(Sigma2.shape) != 2:
            if Mu is None:
                Mu = UnivariateGaussian.mean(X)
            Sigma2 = MultivariateGaussian.covar(X, Mu)

        # Loading parameters from config if available
        if PCA_K is None and self.config.get("pca_dimensions_number"): # give priority to parameters given as function's arguments
            PCA_K = self.config.get("pca_dimensions_number")

        if PCA_Threshold is None and self.config.get("pca_dimensions_variation_loss_threshold"): # give priority to parameters given as function's arguments
            PCA_Threshold = self.config.get("pca_dimensions_variation_loss_threshold")

        if PCA_K is None and PCA_Threshold is None: # default value for PCA_Threshold = 0.01 = 1% of VariationLoss tolerance
            PCA_Threshold = 0.01

        # Backup the weights (because we don't want to lose them nor normalize them, we need them later for classification learning!)
        bak = None
        if 'framerepeat' in X.keys():
            bak = X['framerepeat']

        # Compute the eigenvectors
        PCA_U, PCA_S, PCA_V = PCA.compute_vectors(Sigma2)

        # Find the best K dimensions to minimize the variation loss
        VariationLoss = None
        if PCA_K is None:
            PCA_K, VariationLoss = PCA.find_best_dim(PCA_S, PCA_Threshold, True)

        # Print the variation loss
        VariationLoss = PCA.compute_variation_loss(PCA_S, PCA_K, True)

        # Project X onto the first K eigenvectors (reducing X onto lower dimensions)
        if PCA_K >= len(X.columns):
            print('PCA: Cannot reduce with the specified K/Threshold!')
        else:
            print('PCA: Reducing X to K=%s dimensions.' % str(PCA_K))
            X = PCA.project(X, PCA_U, PCA_K)

        # Put back the weights
        if bak is not None: X['framerepeat'] = bak

        # Note: we should NOT return the mean Mu and covariance Sigma2 since we changed the whole dataset, these have to be recomputed all over again! But this time on a smaller dataset, it should be a lot faster.
        return {'X':  X, 'PCA_K': PCA_K, 'PCA_U': PCA_U, 'PCA_S': PCA_S, 'PCA_V': PCA_V, 'PCA_VariationLoss': VariationLoss, 'Mu': None, 'Sigma2': None} # always return a dict of variables if you want your variables saved durably and accessible later

    ## Compute the SVD from a covariance matrix of the dataset, and returns the eigenvectors and eigenvalues
    # @param Sigma2 Covariance matrix of the dataset X
    # @return U,S,V eigenvectors, eigenvalues and ordered variations over the eigenvectors (from the biggest to the smallest)
    @staticmethod
    def compute_vectors(Sigma2):
        if 'framerepeat' in Sigma2.columns:
            Sigma2 = Sigma2.drop('framerepeat', axis=0).drop('framerepeat', axis=1) # drop the framerepeat key, we don't want to extract eigenvectors on this axis!
        U, S, V = np.linalg.svd(Sigma2) # Compute the eigenvectors and eigenvalues and ordered variations along all those vectors
        V = V.T # because np.linalg.svd() returns V.T and not V, we must put it back in the right transposition
        U = pd.DataFrame(U, index=Sigma2.columns) # Convert U to a DataFrame with meaningful indexes
        return (U,S,V)

    ## Compute the variation loss
    # The variation loss is the variation lost when using the reduced dimensions provided by the K first eigenvectors from the PCA.
    # This is an objective indicator on how much information you lose in the reduction.
    # @param S Matrix S of ordered variations from SVD
    # @param K Number of dimensions you will use in the reduction. How much loss for the K first eigenvectors?
    # @param debug If true, print the variation loss
    # @return VariationLoss Float between 0 and 1. Lower is better. Multiply by 100 to get a variation loss percentage.
    @staticmethod
    def compute_variation_loss(S, K, debug=False):
        VariationLoss = 1 - (S[0:K].sum() / S.sum())
        if debug: print("VariationLoss for K=%s: %g%%" % (str(K), VariationLoss * 100))
        return VariationLoss

    ## Find the best K (number of dimensions) without losing too much variations
    # @param S Matrix S of ordered variations from SVD
    # @param Threshold Maximum Variation Loss tolerated (between 0 and 1, 1 being 100%). At learning, can be used to find the best PCA_K. Default = 0.01 (= 1% tolerated)
    # @param debug If true, print the best K found and the variation loss associated
    # @return list(BestK,VariationLoss) Best K found (number of dimensions to reduce to), and the variation loss associated
    @staticmethod
    def find_best_dim(S, Threshold=0.01, debug=False):
        for K in xrange(len(S)):
            VariationLoss = PCA.compute_variation_loss(S, K)
            if VariationLoss < Threshold:
                BestK = K
                break
        if debug: print("BestK: %s - VariationLoss: %g%%" % (BestK, VariationLoss % 100))
        return (BestK, VariationLoss)

    ## Project/Reduce a dataset X of N dimensions onto K lower dimensions
    # @param X The dataset
    # @param U Eigenvectors from the SVD on the covariance matrix of X
    # @param K Number of dimensions to reduce X to
    # @return Z The reduced/projected dataset of K dimensions
    @staticmethod
    def project(X, U, K):
        X = X.drop('framerepeat', axis=1) # drop the framerepeat of course
        # Project the dataset onto the first K eigenvectors (since the matrixes returned by the SVD are ordered, from the highest variance eigenvectors to the lowest variance ones)
        Z = pd.DataFrame(np.dot(X, U.ix[:, 0:K-1])) # When using Pandas, U.ix[:, 0:K-1] is equal to numpy's U[:, 0:K] (there's an offset of +1 using Pandas, thus we correct it here)
        return Z

    ## Alias for PCA.project()
    @staticmethod
    def reduce(X, U, K):
        return PCA.project(X, U, K)
