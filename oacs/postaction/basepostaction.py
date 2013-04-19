#!/usr/bin/env python
# encoding: utf-8

## @package basepostaction
#
# This contains the base post action class to be used as a template for other post action classes

from oacs.base import BaseClass

## BasePostAction
#
# Base post action class, use this as a template for your post action class
class BasePostAction(BaseClass):

    ## @var config
    # A reference to a ConfigParser object, already loaded

    ## @var parent
    # A reference to the parent object (Runner)

    ## Constructor
    # @param config An instance of the ConfigParser class
    def __init__(self, config=None, parent=None, *args, **kwargs):
        return BaseClass.__init__(self, config, parent, *args, **kwargs)

    ## Do an action
    # @param Any variable
    def action(self, *args, **kwargs):
        return True
