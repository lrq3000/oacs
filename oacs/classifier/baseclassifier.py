#!/usr/bin/env python
# encoding: utf-8

## @package baseclassifier
#
# This contains the base classifier class to be used as a template for other classifiers

from oacs.base import BaseClass
import random

## BaseClassifier
#
# Base classifier class, use this as a template for your classifier algorithm
class BaseClassifier(BaseClass):

    ## @var config
    # A reference to a ConfigParser object, already loaded

    ## @var parent
    # A reference to the parent object (Runner)

    ## Constructor
    # @param config An instance of the ConfigParser class
    def __init__(self, config=None, parent=None, *args, **kwargs):
        return BaseClass.__init__(self, config, parent, *args, **kwargs)

    ## Learn the parameters from a given set X of examples, and labels Y
    # @param X Samples set
    # @param Y Labels set (corresponding to X)
    def learn(self, X=None, Y=None, *args, **kwargs):
        Theta = [1]
        return {'Theta': [1]} # always return a dict of variables if you want your variables saved durably and accessible later

    ## Predict/Classify the probability/class of an example given a set of parameters
    # @param X One unknown example to label
    # @param Theta Set of parameters to use for the prediction/classification (should be outputted by the local method learn() )
    def predict(self, X=None, Theta=None, *args, **kwargs):
        return {"Prediction": random.uniform(0.0,1.0) } # return the class of the sample (here we make no prediction, we just return a random probability between 0 and 1)
