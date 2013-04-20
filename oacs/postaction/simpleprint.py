#!/usr/bin/env python
# encoding: utf-8

## @package simpleprint
#
# This class simply prints a message in the console whenever a positive detection of a cheater occurs

from oacs.postaction.basepostaction import BasePostAction

from subprocess import call

## SimplePrint
#
# Simply prints a message in the console whenever a positive detection of a cheater occurs
class SimplePrint(BasePostAction):

    ## @var config
    # An instance of the ConfigParser object, already loaded

    ## Constructor
    # @param config An instance of the ConfigParser class
    def __init__(self, config=None, *args, **kwargs):
        return BasePostAction.__init__(self, config, *args, **kwargs)

    ## Simply prints a message in the console whenever a positive detection of a cheater occurs
    # @param Cheater Is the player a cheater?
    # @param Playerinfo A dict containing the info of the last detected cheater
    # @param **kwargs(Any_Variable) Any other variable passed in argument will be substituted by its string representation
    def action(self, Cheater=False, Playerinfo=None, debug=False, *args, **kwargs):
        if Cheater: print("Cheater detected!")

        return True
