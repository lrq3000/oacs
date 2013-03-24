#!/usr/bin/env python
# encoding: utf-8

## @package base
#
# This contains the base parser class to be used as a template for other parsers

from oacs.base import BaseClass

## BaseParser
#
# Base input parser, use this as a template for your input parser
class BaseParser(BaseClass):

    ## @var config
    # An instance of the ConfigParser object, already loaded

    ## Constructor
    # @param config An instance of the ConfigParser class
    def __init__(self, config, *args, **kwargs):
        return BaseClass.__init__(self, config, *args, **kwargs)

    ## Load the content of a file and return it
    # @param file Path to the input file to read
    def load(self, file, *args, **kwargs):
        try:
            f = open(file, 'rb') # open in binary mode to avoid line returns translation (else the reading will be flawed!). We have to do it both at saving and at reading.
            content = f.read()
            f.close()
            return content
        except Exception, e:
            print e
            return False
