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
    # A reference to a ConfigParser object, already loaded

    ## @var parent
    # A reference to the parent object (Runner)

    ## Constructor
    # @param config An instance of the ConfigParser class
    def __init__(self, config=None, parent=None, *args, **kwargs):
        return BaseClass.__init__(self, config, parent, *args, **kwargs)

    ## Optimize the dataset
    # @param X Samples set
    def optimize(self, X=None, *args, **kwargs):
        return {'X': X} # always return a dict of variables if you want your variables saved durably and accessible later
