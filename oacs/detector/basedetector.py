#!/usr/bin/env python
# encoding: utf-8

## @package basedetector
#
# This contains the base detector class to be used as a template for other detectors (main loop to detect cheaters using a classifier with learned parameters)

from oacs.base import BaseClass
import random

## BaseDetector
#
# Base detector class, use this as a template for your detector (main loop to detect cheaters using a classifier with learned parameters)
class BaseDetector(BaseClass):

    ## @var config
    # An instance of the ConfigParser object, already loaded

    ## Constructor
    # @param config An instance of the ConfigParser class
    def __init__(self, config, *args, **kwargs):
        return BaseClass.__init__(self, config, *args, **kwargs)

    ## Main loop to check if a player is honest or cheater
    # Note: you can either directly work with X and call the functions by yourself, or you can call them in run executelist and then get the Prediction info
    # @param X Generator yielding one sample at a time. When exhausted, the loop should wait a bit, and then retry to check if X now contains more samples to check.
    # @param Prediction A scalar or a vector of predictions (preferably probabilities, but you are free to do whatever you want, as long as you manage the predictions values properly in your detector)
    def detect(self, X=None, Prediction=None, *args, **kwargs):
        # Assign a random value to Prediction if none is set
        if not Prediction:
            Prediction = random.uniform(0.0,1.0)
        # Random threshold for detection
        if Prediction*Prediction < 0.1:
            cheater = True # the player is a cheater!
        else:
            cheater = False # the player is not a cheater
        # We can return a Playerinfo dict with extended informations identifying the player for futher processing by postaction classes
        Playerinfo = {'cheater': cheater, 'playername': 'John Doe'}
        # Return the result
        return {'Cheater': cheater, 'Playerinfo': Playerinfo} # always return a dict of variables
