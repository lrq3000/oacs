#!/usr/bin/env python
# encoding: utf-8

## @package binarydecider
#
# This contains the binary decider class which just flag cheaters when Prediction is above 0.5

from oacs.decider.basedecider import BaseDecider

## BinaryDecider
#
# Flag cheaters when Prediction is below 0.5 (meaning the player is less probably human than human)
class BinaryDecider(BaseDecider):

    ## @var config
    # A reference to a ConfigParser object, already loaded

    ## @var parent
    # A reference to the parent object (Runner)

    ## Constructor
    # @param config An instance of the ConfigParser class
    def __init__(self, config=None, parent=None, *args, **kwargs):
        return BaseDecider.__init__(self, config, parent, *args, **kwargs)

    ## Flag cheaters when Prediction is below 0.5
    # Note: you can either directly work with X and call the functions by yourself, or you can call them in run executelist and then get the Prediction info
    # @param Prediction A scalar or a vector of predictions (preferably probabilities, but you are free to do whatever you want, as long as you manage the predictions values properly in your decider)
    # @return DictOfVars Should at least return a dict of variables containing only at least 'Cheater' (True or False)
    def decide(self, Prediction=None, *args, **kwargs):
        if Prediction < 0.5:
            cheater = True # the player is a cheater!
        else:
            cheater = False # the player is not a cheater

        # Return the result
        return {'Cheater': cheater} # always return a dict of variables if you want your variables saved durably and accessible later if you want your variables saved durably and accessible later
