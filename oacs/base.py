#!/usr/bin/env python
# encoding: utf-8

## @package base
#
# This contains the base classes that are used by most other classes (in subfolders)

## BaseClass
#
# Base class for most other classes (in subfolders)
class BaseClass(object):

    ## @var config
    # An instance of the ConfigParser object, already loaded

    ## Constructor
    # @param config An instance of the ConfigParser class
    def __init__(self, config, *args, **kwargs):
        if not self.loadconfig(config):
            print('CRITICAL ERROR : COULD NOT LOAD CONFIG')
            raise SystemExit(220)

    ## Register the configuration to be directly accessible as a variable inside this object
    # @param config An instance of the ConfigParser class
    def loadconfig(self, config, *args, **kwargs):
        if not config:
            return False

        self.config = config

        return True