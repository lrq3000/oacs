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
    def __init__(self, config, *args, **kwargs):
        return BasePreOptimization.__init__(self, config, *args, **kwargs)

    ## Normalize the X dataset into a normal distribution (mean = 0, variance = 1)
    # @param X Samples set
    def optimize(self, X=None, Mu=None, Sigma2=None, *args, **kwargs):
        return {'X': ((X - X.mean()) / X.std()) } # always return a dict of variables
