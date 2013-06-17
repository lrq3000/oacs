#!/usr/bin/env python
# encoding: utf-8

## @package basedecider
#
# This contains the base decider class to be used as a template for other deciders (main loop to detect cheaters using a classifier with learned parameters)

from oacs.base import BaseClass
import random
import pandas as pd

## BaseDecider
#
# Base decider class, use this as a template for your decider (main loop to decide if someone is a cheaters based on a classifier's prediction)
class BaseDecider(BaseClass):

    ## @var config
    # A reference to a ConfigParser object, already loaded

    ## @var parent
    # A reference to the parent object (Runner)

    ## Constructor
    # @param config An instance of the ConfigParser class
    def __init__(self, config=None, parent=None, *args, **kwargs):
        return BaseClass.__init__(self, config, parent, *args, **kwargs)

    ## Decide whether a player is cheating based on a classifier's prediction value
    # Note: you can either directly work with X and call the functions by yourself, or you can call them in run executelist and then get the Prediction info
    # @param Prediction A scalar or a vector of predictions (preferably probabilities, but you are free to do whatever you want, as long as you manage the predictions values properly in your decider)
    # @param Threshold Below this threshold, a player is considered to be a cheater (likelihood of humanly actions is low)
    # @param CompDir Direction of the comparison operator (either 'gt' for greater than the threshold, either 'lt' for lesser than the threshold)
    # @return DictOfVars Should at least return a dict of variables containing only at least 'Cheater' (True or False)
    def decide(self, Prediction=None, Threshold=0.5, CompDir='lt', *args, **kwargs):

        # Debug mode: Assign a random value to Prediction if none is set
        if self.config.config.get('debug'):
            Prediction = random.uniform(0.0,1.0)
        if self.config.config.get('debug', None): print(Prediction)

        if self.config.config.get('decider_threshold', None) is not None:
            Threshold = self.config.config.get('decider_threshold')

        #print(Prediction)
        # If the player is below the threshold, we flag him as a cheater
        if CompDir == 'gt' and Prediction > Threshold: # "Greater than" comparison
            cheater = True # the player is a cheater!
        elif CompDir == 'lt' and Prediction < Threshold: # "Less than" comparison
            cheater = True # the player is a cheater!
        else:
            cheater = False # the player is not a cheater

        # Return the result
        return {'Cheater': cheater} # always return a dict of variables if you want your variables saved durably and accessible later
