#!/usr/bin/env python
# encoding: utf-8

## @package basedetector
#
# This contains the base detector class to be used as a template for other detectors (main loop to detect cheaters using a classifier with learned parameters)

from oacs.base import BaseClass
import random
import pandas as pd

## BaseDetector
#
# Base detector class, use this as a template for your detector (main loop to detect cheaters using a classifier with learned parameters)
class BaseDetector(BaseClass):

    ## @var config
    # A reference to a ConfigParser object, already loaded

    ## @var parent
    # A reference to the parent object (Runner)

    ## Constructor
    # @param config An instance of the ConfigParser class
    def __init__(self, config=None, parent=None, *args, **kwargs):
        return BaseClass.__init__(self, config, parent, *args, **kwargs)

    ## Main loop to check if a player is honest or cheater
    # Note: you can either directly work with X and call the functions by yourself, or you can call them in run executelist and then get the Prediction info
    # @param X Generator yielding one sample at a time.
    # @param Prediction A scalar or a vector of predictions (preferably probabilities, but you are free to do whatever you want, as long as you manage the predictions values properly in your detector)
    # @return DictOfVars Should at least return a dict of variables containing 'Cheater' and if possible 'Playerinfo' with extended player informations identifying the player (you can call BaseDetector._makePlayerinfo() to do that). It is advised that this method also write down the result of each positive (cheater) detection in a file.
    def detect(self, X=None, Prediction=None, X_raw=None, *args, **kwargs):
        # Assign a random value to Prediction if none is set
        if not Prediction:
            Prediction = random.uniform(0.0,1.0)
        # Random threshold for detection
        if Prediction*random.uniform(0.0,1.0) < 0.05:
            cheater = True # the player is a cheater!
        else:
            cheater = False # the player is not a cheater

        # Make the Playerinfo (extended player's infos, necessary for postactions)
        Playerinfo = self._makePlayerinfo(Cheater=cheater, X_raw=X_raw)

        # Return the result
        return {'Cheater': cheater, 'Playerinfo': Playerinfo} # always return a dict of variables

    ## Make Playerinfo (extended player's infos, necessary for postactions)
    def _makePlayerinfo(self, Cheater=None, X_raw=None, *args, **kwargs):
        # We can return a Playerinfo dict with extended informations identifying the player for futher processing by postaction classes
        Playerinfo = {'cheater': Cheater}
        if X_raw is not None and type(X_raw) == pd.Series: Playerinfo.update(X_raw.to_dict()) # add all the informations available in Playerinfo
        return Playerinfo
