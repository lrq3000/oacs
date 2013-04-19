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
    # A reference to a ConfigParser object, already loaded

    ## @var parent
    # A reference to the parent object (Runner)

    ## Constructor
    # @param config An instance of the ConfigParser class
    def __init__(self, config=None, parent=None, *args, **kwargs):
        if not self.loadconfig(config):
            print('CRITICAL ERROR : COULD NOT LOAD CONFIG IN CLASS %s' % self.__class__)
            raise SystemExit(220)
        if parent:
            self.parent = parent
        return object.__init__(self)

    ## Register the configuration to be directly accessible as a variable inside this object
    # @param config An instance of the ConfigParser class, or path to the config file
    def loadconfig(self, config, *args, **kwargs):

        # No config, we quit
        if not config:
            return False

        # If we were supplied a string, we consider it to be the path to the config file to load
        if isinstance(config, basestring):
            # Loading the config
            from configparser import ConfigParser
            self.config = ConfigParser()
            self.config.init(config)
            self.config.load(*args)
        # Else we already have a loaded config object, we just reference it locally
        else:
            self.config = config

        return True