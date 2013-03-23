#!/usr/bin/env python
# encoding: utf-8

## @package interframeparser
#
# Parse the data from a file containing interframes in JSON format

from oacs.inputparser.jsonparser import JsonParser

from auxlib import *
import re, os

json = import_module('ujson')
if json is None:
    json = import_module('json')
    if json is None:
        raise RuntimeError('Unable to find a json implementation')

## InterframeParser
#
# Parse the data from a file containing interframes in JSON format
class InterframeParser(JsonParser):
    ## @var config
    # An instance of the ConfigParser object, already loaded

    ## Constructor
    # @param config An instance of the ConfigParser class
    def __init__(self, config, *args, **kwargs):
        return JsonParser.__init__(self, config, *args, **kwargs)

    ## Load the content of a file as JSON and return a Python object corresponding to the JSON tree
    # @param file Path to the input file to read
    def load(self, file, addrootarray=False, *args, **kwargs):
        jsoncontent = JsonParser.load(file, addrootarray, *args, **kwargs)
        