#!/usr/bin/env python
# encoding: utf-8

## @package multivariategaussian
#
# Multivariate gaussian AIS (Artificial Immune System) classifier.

from oacs.classifier.univariategaussian import UnivariateGaussian
import random
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
        Sigma2 = self.covar(Xt, Mu, 'framerepeat') # Vector of variances or Covariance matrix
        return {'Mu': Mu, 'Sigma2': Sigma2} # always return a dict of variables

    ## Multivariate gaussian prediction of the probability/class of an example given a set of parameters (weighted mean and covariance matrix)
    # @param X One unknown example to label
    # @param Mu Weighted mean of X
    # @param Sigma2 Covariance matrix of X
    # TODO: compatibility with more than one sample (detect type==pdSseries)?
    def predict(self, X=None, Mu=None, Sigma2=None, *args, **kwargs):
        if 'framerepeat' in X:
            X = X.drop(['framerepeat'])
            Sigma2 = Sigma2.drop(['framerepeat'], axis=0) # drop in both axis
            Sigma2 = Sigma2.drop(['framerepeat'], axis=1)
            Mu = Mu.drop(['framerepeat'])

        # if sigma2 is a vector, we convert it to a (covariance) matrix (filled with only values on the diagonal)
        if type(Sigma2) == pd.Series:
            Sigma2 = np.diag(Sigma2)
            Sigma2 = pd.DataFrame(Sigma2)

        n = len(Mu.keys()) #X.shape[0]
        xm = X-Mu # X difference to the mean
        xm = xm.fillna(0) # if we have one NA, the whole result of all values will be NA
        Pred = (2*pi)**(-n/2) * np.linalg.det(Sigma2)**0.5 * exp(-0.5 * xm.T.dot(np.linalg.pinv(Sigma2)).dot(xm))

        return {'Prediction': Pred} # return the class of the sample(s)

    ## Compute the weighted mean of the dataset
    # @param X Samples dataset
    # @param weights Vector/Series of weights (ie: number of times one sample has to be repeated) - default: X['framerepeat']
    def mean(self, X, weights=None):
        return UnivariateGaussian.mean(X, weights)

    ## Compute the weighted covariance matrix of the dataset
    # Alternative to pandas.DataFrame.cov(), because pandas's and numpy's cov() can't account for weights (if you set mean = X.mean(), then you'll get the exact same result as X.cov())
    # @param X One example or a dataset of examples (must the same columns/keys as mean)
    # @param mean Weighted mean (must have the same columns/keys as X, else you will get a weird result, because pandas will still try to adapt and things will get really messed up!)
    # @param weights Name of the weights column to remove from the final result (else it may flaw the computation of the prediction)
    # TODO: bigdata iteration version (detect generator?) - WARNING: then the division by m-1 must be done at the end of all the sums of all sigma2 of every x sample!
    def covar(self, X, mean, weights=None):
        if weights is None: weights = 'framerepeat'
        if weights in X.keys() and weights not in mean.keys():
            if type(X) == pd.Series:
                ax = 0
            else:
                ax = 1
            X = X.drop(weights, axis=ax)
        xm = X-mean # xm = X diff to mean
        xm = xm.fillna(0)
        if type(X) == pd.Series:
            sigma2 = np.outer(xm.T, xm); # force matrix multiplication outer dot product (else if you use np.dot() or pandas.dot(), it will align by the indexes)
        else:
            m = X.shape[0]
            sigma2 = 1./(m-1) * xm.T.dot(xm);

        return sigma2
