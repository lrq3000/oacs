#!/usr/bin/env python
# encoding: utf-8

## @package univariategaussian
#
# Univariate gaussian AIS (Artificial Immune System) classifier.

from oacs.classifier.baseclassifier import BaseClassifier
import random
import numpy as np
import pandas as pd
from numpy import pi, exp

## UnivariateGaussian
#
# Univariate gaussian AIS (Artificial Immune System) classifier class, this will return a set of parameters: a vector of means Mu, and a vector of variances Sigma2 for each feature
class UnivariateGaussian(BaseClassifier):

    ## @var config
    # An instance of the ConfigParser object, already loaded

    ## Constructor
    # @param config An instance of the ConfigParser class
    def __init__(self, config=None, *args, **kwargs):
        return BaseClassifier.__init__(self, config, *args, **kwargs)

    ## Learn the parameters from a given set X of examples, and labels Y
    # @param X Samples set
    # @param Y Labels set (corresponding to X)
    def learn(self, X=None, Y=None, *args, **kwargs):
        Yt = Y[Y==0].dropna() # get the list of non-anomalous examples
        Xt = X.iloc[Yt.index] # filter out anomalous examples and keep only non-anomalous ones
        Mu = UnivariateGaussian.mean(Xt, Xt['framerepeat']) # Mean
        Sigma2 = UnivariateGaussian.variance(Xt, Mu, Xt['framerepeat']) # Vector of variances or Covariance matrix
        return {'Mu': Mu, 'Sigma2': Sigma2} # always return a dict of variables if you want your variables saved durably and accessible later

    ## Univariate gaussian prediction of the probability/class of an example given a set of parameters (weighted mean and vector of standard deviations)
    # @param X One unknown example to label
    # @param Mu Weighted mean of X
    # @param Sigma2 Covariance matrix of X
    def predict(self, X=None, Mu=None, Sigma2=None, *args, **kwargs):
        # Univariate gaussian density estimation
        Pred = (1/(2*pi*Sigma2)**0.5) * exp(-(X-Mu)/(2*Sigma2))
        if 'framerepeat' in Pred.keys():
            Pred = Pred.drop(['framerepeat'])
        # Compute the product of all probabilities (p1 = proba of feature 1 being normal; p1*p2*p3*...*pn)
        Pred = Pred.prod()

        return {'Prediction': Pred} # return the class of the sample(s)

    ## Compute the weighted mean of the dataset
    # @param X Samples dataset
    # @param weights Vector/Series of weights (ie: number of times one sample has to be repeated) - default: X['framerepeat']
    # TODO: bigdata iteration version (detect generator?)
    @staticmethod
    def mean(X, weights=None):
        if weights is None: weights = X['framerepeat']
        mean = np.average(X, axis=0, weights=weights)
        mean = pd.Series(mean, index=list(X.keys()))
        return mean

    ## Alternative way to compute the weighted mean of the dataset without using Numpy (ends up being slower)
    # @param X Samples dataset
    # @param weights Vector/Series of weights (ie: number of times one sample has to be repeated) - default: X['framerepeat']
    @staticmethod
    def mean_alt(X, weights=None):
        def applyweight(serie):
            if weights is not None:
                weight = serie[weights]
            else:
                weight = serie['framerepeat']
            #s2 = serie.drop(['framerepeat'])
            s = serie * weight
            s['framerepeat'] = weight
            return s

        if 'framerepeat' in X.keys():
            X = X.apply(applyweight, axis=1)

        mean = X.sum().astype(float) / X.ix[:,'framerepeat'].sum()
        return mean

    ## Compute the weighted unbiased variance of each feature for a given dataset
    # @param X Samples dataset
    # @param mean Weighted mean
    # @param weights Vector/Series of weights (ie: number of times one sample has to be repeated) - default: X['framerepeat']
    # TODO: bigdata iteration version (detect generator?)
    @staticmethod
    def variance(X, mean, weights=None):
        if weights is None: weights = X['framerepeat']
        squareddiff = X-mean
        squareddiff = squareddiff * squareddiff # TODO: bug with Pandas/Numpy: if **2 produce this: https://github.com/pydata/pandas/issues/3407
        variance = squareddiff.T.dot(weights) * ( 1.0 / (weights.sum()-1) ) # DataFrames and Series are implicitly aligned by index
        #sigma = variance ** 0.5
        return variance

    ## Alternative way to compute the weighted unbiased variance of each feature for a given dataset using numpy instead of pandas (this is actually slower)
    # @param X Samples dataset
    # @param mean Weighted mean
    # @param weights Vector/Series of weights (ie: number of times one sample has to be repeated) - default: X['framerepeat']
    @staticmethod
    def variance_alt(X, mean, weights=None):
        if weights is None: weights = X['framerepeat']
        variance = np.dot(weights.tolist(), ((X-mean.tolist())**2))/ (weights.sum()-1)  # Fast and numerically precise
        #sigma = np.sqrt(variance)
        variance = pd.Series(variance, index=list(X.keys()))
        return variance
