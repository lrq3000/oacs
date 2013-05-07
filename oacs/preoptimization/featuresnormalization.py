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
    def optimize(self, X=None, Mu=None, Sigma2=None, *args, **kwargs):
        # TODO: Pandas bug: if you do / X.std() instead of * (1.0/X.std()), python will loop and use 25 percent of the CPU, even when your application finished processing! This is a pandas or numpy bug. Avoid this bug by doing *(1.0/var) instead of dividing by var, or *var**-1, the results will be the same. https://github.com/pydata/pandas/issues/3407
        return {'X':  (X - X.mean()) * (1.0/X.std()) } # always return a dict of variables if you want your variables saved durably and accessible later
