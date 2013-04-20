#!/usr/bin/env python
# encoding: utf-8

## @package weightedfeaturesnormalization
#
# Normalize the X dataset into a normal distribution (mean = 0, variance = 1) using weighted mean and variance

from oacs.preoptimization.basepreoptimization import BasePreOptimization
from oacs.classifier.univariategaussian import UnivariateGaussian
import pandas as pd

## FeaturesNormalization
#
# Normalize the X dataset into a normal distribution (mean = 0, variance = 1) using weighted mean and variance
class WeightedFeaturesNormalization(BasePreOptimization):

    ## @var config
    # An instance of the ConfigParser object, already loaded

    ## Constructor
    # @param config An instance of the ConfigParser class
    def __init__(self, config=None, *args, **kwargs):
        return BasePreOptimization.__init__(self, config, *args, **kwargs)

    ## Normalize the X dataset into a normal distribution (mean = 0, variance = 1)
    # @param X Samples set
    def optimize(self, X=None, Mu=None, Sigma2=None, *args, **kwargs):
        # Compute the weighted mean
        if Mu is None: # Only if it is not already computed
            Mu = UnivariateGaussian.mean(X)
        # Compute the variance
        if Sigma2 is None:
            Sigma2 = UnivariateGaussian.variance(X, Mu)
        # Backup the weights (because we don't want to lose them nor normalize them, we need them later for classification learning!)
        if 'framerepeat' in X.keys():
            bak = X['framerepeat']
        # Compute the normalized dataset
        X_std = (X - Mu) * (1.0/Sigma2**0.5) # TODO: Bug Pandas or Numpy: never do X / var, but X * (1.0/var) or X * var**-1, else if you divide, python will continue to run in the background and use 25 percent CPU! https://github.com/pydata/pandas/issues/3407
        # Put back the weights
        X_std['framerepeat'] = bak
        # Return the result
        return {'X': X_std} # always return a dict of variables
