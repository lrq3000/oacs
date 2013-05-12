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
        # Avoiding NaNs
        Sigma2.fillna(1) # Simplification: if for a feature there's no variance at all (= 0), the feature will be NaN. This happens for example if there's no really any recorded data for the feature yet. We don't want that because it will break classifiers' predictions probabilities. Thus we set variance = 1 for these so that we say it's already a normally-spread distribution (thus below only the mean will normalize the feature, it's already centered)
        Sigma2[Sigma2 == 0.0] = 1 # Set 0 values to 1 (because else we will divide by zero, and get NaN!)
        # Backup the weights (because we don't want to lose them nor normalize them, we need them later for classification learning!)
        if 'framerepeat' in X.keys():
            bak = X['framerepeat']
        # Compute the normalized dataset
        X_std = (X - Mu) * (1.0/Sigma2**0.5) # TODO: Bug Pandas or Numpy: never do X / var, but X * (1.0/var) or X * var**-1, else if you divide, python will continue to run in the background and use 25 percent CPU! https://github.com/pydata/pandas/issues/3407
        # Put back the weights
        X_std['framerepeat'] = bak
        # Return the result
        return {'X': X_std} # always return a dict of variables if you want your variables saved durably and accessible later
