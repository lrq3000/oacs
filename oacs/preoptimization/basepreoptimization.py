#!/usr/bin/env python
# encoding: utf-8

## @package basepreoptimization
#
# This contains the base pre optimization class to be used as a template for other data pre optimizers

from oacs.base import BaseClass

## BasePreOptimization
#
# Base pre optimization class, use this as a template for your classifier algorithm
class BasePreOptimization(BaseClass):

    ## @var config
    # An instance of the ConfigParser object, already loaded

    ## Constructor
    # @param config An instance of the ConfigParser class
    def __init__(self, config, *args, **kwargs):
        return BaseClass.__init__(self, config, *args, **kwargs)

    ## Optimize the dataset
    # @param X Samples set
    def optimize(self, X=None, *args, **kwargs):
        return {'X': X} # always return a dict of variables
