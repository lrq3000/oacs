#!/usr/bin/env python
# encoding: utf-8

## @package multivariategaussian
#
# Multivariate gaussian AIS (Artificial Immune System) classifier.

from oacs.classifier.univariategaussian import UnivariateGaussian
import numpy as np
import pandas as pd
from numpy import pi, exp

## MultivariateGaussian
#
# Multivariate gaussian AIS (Artificial Immune System) classifier class, this will return a set of parameters: a vector of means Mu, and a covariance matrix Sigma2
# This AIS classifier can catch any correlation between any feature
class MultivariateGaussian(UnivariateGaussian):

    ## @var config
    # An instance of the ConfigParser object, already loaded

    ## Constructor
    # @param config An instance of the ConfigParser class
    def __init__(self, config=None, *args, **kwargs):
        return UnivariateGaussian.__init__(self, config, *args, **kwargs)

    ## Learn the parameters from a given set X of examples, and labels Y
    # @param X Samples set
    # @param Y Labels set (corresponding to X)
    def learn(self, X=None, Y=None, *args, **kwargs):
        Yt = Y[Y==0].dropna() # get the list of non-anomalous examples
        Xt = X.iloc[Yt.index] # filter out anomalous examples and keep only non-anomalous ones
        Mu = self.mean(Xt, Xt['framerepeat']) # Mean
        Sigma2 = MultivariateGaussian.covar(Xt, Mu, 'framerepeat') # Vector of variances or Covariance matrix
        return {'Mu': Mu, 'Sigma2': Sigma2} # always return a dict of variables if you want your variables saved durably and accessible later

    ## Multivariate gaussian prediction of the probability/class of an example given a set of parameters (weighted mean and covariance matrix)
    # @param X One unknown example to label
    # @param Mu Weighted mean of X
    # @param Sigma2 Covariance matrix of X
    # TODO: compatibility with more than one sample (detect type==pdSseries)?
    def predict(self, X=None, Mu=None, Sigma2=None, *args, **kwargs):
        return MultivariateGaussian._predict(X=X, Mu=Mu, Sigma2=Sigma2)

    ## Multivariate gaussian prediction of the probability/class of an example given a set of parameters (weighted mean and covariance matrix)
    # Note: we use a proxy method predict so that we can put this one as a staticmethod, and thus be called by other classes (since the code here is very generic)
    # @param X One unknown example to label
    # @param Mu Weighted mean of X
    # @param Sigma2 Covariance matrix of X
    # TODO: compatibility with more than one sample (detect type==pdSseries)?
    @staticmethod
    def _predict(X=None, Mu=None, Sigma2=None, *args, **kwargs):
        if 'framerepeat' in X.keys():
            if type(X) == pd.Series:
                X = X.drop(['framerepeat']) # axis will produce a bug with Series
            else:
                X = X.drop(['framerepeat'], axis=1)
        if 'framerepeat' in Sigma2.keys():
            Sigma2 = Sigma2.drop(['framerepeat'], axis=0) # drop in both axis
            Sigma2 = Sigma2.drop(['framerepeat'], axis=1)
        if 'framerepeat' in Mu.keys():
            Mu = Mu.drop(['framerepeat'])

        # if sigma2 is a vector, we convert it to a (covariance) matrix (filled with only values on the diagonal)
        if type(Sigma2) == pd.Series:
            Sigma2 = np.diag(Sigma2)
            Sigma2 = pd.DataFrame(Sigma2)

        n = len(Mu.keys()) #X.shape[0]
        xm = X-Mu # X difference to the mean
        xm = xm.fillna(0) # if we have one NA, the whole result of all values will be NA
        if type(X) == pd.Series:
            Pred = (2*pi)**(-n/2) * np.linalg.det(Sigma2)**0.5 * exp(-0.5 * xm.T.dot(np.linalg.pinv(Sigma2)).dot(xm))
        else:
            #T = np.outer(xm.dot(np.linalg.pinv(Sigma2)), xm.T) #debug - produce Memory Error even with relatively small sets!
            #print T.shape #debug
            #print xm.shape #debug
            #print(T.head())
            Pred = (2*pi)**(-n/2) * np.linalg.det(Sigma2)**0.5 * exp(-0.5 * (xm.dot(np.linalg.pinv(Sigma2)) * xm).sum(axis=1)) # TODO: fix this, it does not work with more than one sample to test at a time

        return {'Prediction': Pred} # return the class of the sample(s)

    ## Compute the weighted mean of the dataset
    # @param X Samples dataset
    # @param weights Vector/Series of weights (ie: number of times one sample has to be repeated) - default: X['framerepeat']
    def mean(self, X, weights=None):
        return UnivariateGaussian.mean(X, weights)

    ## Compute the unbiased weighted sample covariance matrix of the dataset
    # Alternative to pandas.DataFrame.cov(), because pandas's and numpy's cov() can't account for weights (if you set mean = X.mean() and weights = None, then you'll get the exact same result as X.cov())
    # Note: this works ONLY with unnormalized, integer weights >= 0 representing the number of occurrences of an observation (number of "repeat" of one row in the sample)
    # LaTeX equation: \Sigma=\frac{1}{\sum_{i=1}^{N}w_i - 1}\sum_{i=1}^N w_i \left(x_i - \mu^*\right)^2
    # @param X One example or a dataset of examples (must the same columns/keys as mean)
    # @param mean Weighted mean (must have the same columns/keys as X, else you will get a weird result, because pandas will still try to adapt and things will get really messed up!)
    # @param weights Name of the weights column to remove from the final result (else it may flaw the computation of the prediction)
    # TODO: bigdata iteration version (detect generator?) - WARNING: then the division by m-1 must be done at the end of all the sums of all sigma2 of every x sample!
    @staticmethod
    def covar(X, mean, weights=None):
        if weights is None: weights = 'framerepeat'
        w = None
        if weights in X.keys(): w = X[weights] # backing up the keys
        if weights in X.keys() and weights not in mean.keys():
            if type(X) == pd.Series:
                ax = 0
            else:
                ax = 1
            X = X.drop(weights, axis=ax)
        xm = X-mean # xm = X diff to mean
        xm = xm.fillna(0) # fill nan with 0 because anyway 0 will give a 0 covariance's coordinate (which means in practical that it is null), but the computation of other covariance's coordinates will be OK (while if you have NaNs you would end up with a covariance matrix filled with NaNs)
        # BigData alternative: compute the covariance one sample at a time (one row with several columns representing different variables)
        #if type(X) == pd.Series:
        #    sigma2 = np.outer(xm.T, xm); # force matrix multiplication outer product (else if you use np.dot() or pandas.dot(), it will align by the indexes and make the dot product)
        #else:

        # If there are weights, compute the unbiased weighted sample covariance
        if w is not None:
            sigma2 = 1./(w.sum()-1) * xm.mul(w, axis=0).T.dot(xm);
        # Else we compute the unbiased sample covariance (without weights)
        else:
            m = X.shape[0]
            sigma2 = 1./(m-1) * xm.T.dot(xm); # Sigma2 = 1/m * X' * X

        return sigma2
