#!/usr/bin/env python
# encoding: utf-8

## @package featuresnormalization
#
# Normalize the X dataset into a normal distribution (mean = 0, variance = 1)

from oacs.preoptimization.basepreoptimization import BasePreOptimization
from oacs.classifier.univariategaussian import UnivariateGaussian
import pandas as pd

## FeaturesNormalization
#
# Normalize the X dataset into a normal distribution (mean = 0, variance = 1)
class FeaturesNormalization(BasePreOptimization):

    ## @var config
    # An instance of the ConfigParser object, already loaded

    ## Constructor
    # @param config An instance of the ConfigParser class
    def __init__(self, config=None, *args, **kwargs):
        return BasePreOptimization.__init__(self, config, *args, **kwargs)

    ## Normalize the X dataset into a normal distribution (mean = 0, variance = 1)
    # @param X Samples set
    # @param Nonstd_Mu At detection, you can reload the previously learnt parameter here
    # @param Nonstd_Sigma2 At detection, you can reload the previously learnt parameter here
    def optimize(self, X=None, Nonstd_Mu=None, Nonstd_Sigma2=None, *args, **kwargs):
        # TODO: Pandas bug: if you do / X.std() instead of * (1.0/X.std()), python will loop and use 25 percent of the CPU, even when your application finished processing! This is a pandas or numpy bug. Avoid this bug by doing *(1.0/var) instead of dividing by var, or *var**-1, the results will be the same. https://github.com/pydata/pandas/issues/3407

        # Either at learning we compute the mean and std, or either at detection we reload the learnt mean and std
        if Nonstd_Mu is None:
            Nonstd_Mu = X.mean()
        if Nonstd_Sigma2 is None:
            Nonstd_Sigma2 = X.std()

        return {'X':  (X - Nonstd_Mu) * (1.0/Nonstd_Sigma2), 'Nonstd_Mu': Nonstd_Mu, 'Nonstd_Sigma2': Nonstd_Sigma2} # always return a dict of variables if you want your variables saved durably and accessible later
