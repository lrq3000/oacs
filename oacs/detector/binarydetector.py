#!/usr/bin/env python
# encoding: utf-8

## @package binarydetector
#
# This contains the binary detector class which just flag cheaters when Prediction is above 0.5

from oacs.base import BaseClass
import random
import pandas as pd

## BinaryDetector
#
# Flag cheaters when Prediction is 1
class BinaryDetector(BaseDetector):

    ## @var config
    # A reference to a ConfigParser object, already loaded

    ## @var parent
    # A reference to the parent object (Runner)

    ## Constructor
    # @param config An instance of the ConfigParser class
    def __init__(self, config=None, parent=None, *args, **kwargs):
        return BaseDetector.__init__(self, config, parent, *args, **kwargs)

    ## Flag cheaters when Prediction is above 0.5
    # Note: you can either directly work with X and call the functions by yourself, or you can call them in run executelist and then get the Prediction info
    # @param X Generator yielding one sample at a time.
    # @param Prediction A scalar or a vector of predictions (preferably probabilities, but you are free to do whatever you want, as long as you manage the predictions values properly in your detector)
    # @return DictOfVars Should at least return a dict of variables containing 'Cheater' and if possible 'Playerinfo' with extended player informations identifying the player (you can call BaseDetector._makePlayerinfo() to do that). It is advised that this method also write down the result of each positive (cheater) detection in a file.
    def detect(self, Prediction=None, X_raw=None, *args, **kwargs):
        if Prediction >= 0.5:
            cheater = True # the player is a cheater!
        else:
            cheater = False # the player is not a cheater

        # Make the Playerinfo (extended player infos, necessary for postactions)
        Playerinfo = BaseDetector._makePlayerinfo(Cheater=cheater, X_raw=X_raw)

        # Return the result
        return {'Cheater': cheater, 'Playerinfo': Playerinfo} # always return a dict of variables
