#!/usr/bin/env python
# encoding: utf-8

## @package interframeparserjson
#
# Parse the data from a file containing interframes in JSON format

from oacs.inputparser.jsonparser import JsonParser

from oacs.auxlib import *
import re, os

json = import_module('ujson')
if json is None:
    json = import_module('json')
    if json is None:
        raise RuntimeError('Unable to find a json implementation')

## InterframeParser
#
# Parse the data from a file containing interframes in JSON format
class InterframeParserJson(JsonParser):
    ## @var config
    # An instance of the ConfigParser object, already loaded

    ## Constructor
    # @param config An instance of the ConfigParser class
    def __init__(self, config, *args, **kwargs):
        return JsonParser.__init__(self, config, *args, **kwargs)

    ## Load the whole content of a file containing interframes in JSON format and return pandas's DataFrames
    # @param file Path to the input file to read
    # @param addrootarray Set to True if the json was outputted line-by-line, and we need to add a root array to "glue" them all
    def load(self, file=None, addrootarray=True, *args, **kwargs):
        jsoncontent = JsonParser.load(self, file, addrootarray, *args, **kwargs)
        return (X_raw, X, Y_raw, Y) # must always return X_raw, X, Y_raw and Y

    ## Read interframes one-line-by-one and return a pandas's DataFrame (this is a generator)
    # @param file Path to the input file to read
    # @param addrootarray Set to True if the json was outputted line-by-line, and we need to add a root array to "glue" them all
    def read(self, file=None, addrootarray=False, *args, **kwargs):
        yield (X_raw, X, Y_raw, Y)

    ## Reset the cursor position to 0 (read the file back from the beginning)
    def resetpos(self, *args, **kwargs):
        BaseParser.resetpos(self, *args, **kwargs)

    ## Set the cursor position to read the file from a specified byte
    def setpos(self, pos=0, *args, **kwargs):
        BaseParser.setpos(self, pos, *args, **kwargs)
