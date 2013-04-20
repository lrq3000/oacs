#!/usr/bin/env python
# encoding: utf-8

## @package jsonparser
#
# General purpose JSON parser

from oacs.inputparser.baseparser import BaseParser

from oacs.auxlib import *
import re, os

json = import_module('ujson')
if json is None:
    json = import_module('json')
    if json is None:
        raise RuntimeError('Unable to find a json implementation')

## JsonParser
#
# General purpose JSON parser
class JsonParser(BaseParser):

    ## Private usage regexp to add missing commas between each object
    reg = re.compile(r"^(.+)$", re.MULTILINE)

    ## @var config
    # An instance of the ConfigParser object, already loaded

    ## Constructor
    # @param config An instance of the ConfigParser class
    def __init__(self, config=None, *args, **kwargs):
        return BaseParser.__init__(self, config, *args, **kwargs)

    ## Load the whole content of a file at once as JSON and return a Python object corresponding to the JSON tree
    # @param file Path to the input file to read
    # @param addrootarray Set to True if the json was outputted line-by-line, and we need to add a root array to "glue" them all
    def load(self, file=None, addrootarray=True, *args, **kwargs):
        # Read the file (the parent object provides a common and exception-handled way to load an entire file at once, so we don't have to care about that)
        jsonraw = BaseParser.load(self, file, addrootarray, *args, **kwargs)

        # If the json was outputted line-by-line, we need to add a root array to "glue" them all
        if (addrootarray):
            jsonraw = os.linesep.join([s for s in jsonraw.splitlines() if s]) # remove empty lines
            jsonraw = self.reg.sub(r'\1,', jsonraw) # add the missing commas between the objects in the root array
            jsonraw = jsonraw.rstrip(',') # remove the last comma
            jsonraw = "[%s]" % jsonraw # convert to a json array of json objects (just by enclosing in [])

        # convert the json string into a json object (ie: a native python dict)
        jsoncontent = json.loads( jsonraw )

        # return the result
        return jsoncontent

    ## Read a file line-by-line and return the content as a JSON construct (ie: Python dict) (this is a generator)
    # @param file Path to the input file to read
    # @param addrootarray Set to True if the json was outputted line-by-line, and we need to add a root array to "glue" them all
    def read(self, file=None, addrootarray=False, *args, **kwargs):
        # Read the file (the parent object provides a common and exception-handled way to read a file line-by-line, so we don't have to care about that)
        for jsonraw in BaseParser.read(self, file, addrootarray, *args, **kwargs):

            # If the json was outputted line-by-line, we need to add a root array to "glue" them all
            if (addrootarray):
                jsonraw = os.linesep.join([s for s in jsonraw.splitlines() if s]) # remove empty lines
                jsonraw = reg.sub(r'\1,', jsonraw) # add the missing commas between the objects in the root array
                jsonraw = jsonraw.rstrip(',') # remove the last comma
                jsonraw = "[%s]" % jsonraw # convert to a json array of json objects (just by enclosing in [])

            # convert the json string into a json object (ie: a native python dict)
            jsoncontent = json.loads( jsonraw )

            # return the result
            yield jsoncontent

    ## Save a JSON construct, UNUSED
    def save(self, jsoncontent, jsonfile, *args, **kwargs):
        with open(jsonfile, 'wb') as f: # open in binary mode to avoid line returns translation (else the reading will be flawed!). We have to do it both at saving and at reading.
            f.write( json.dumps(jsoncontent, sort_keys=True, indent=4) ) # write the file as a json serialized string, but beautified to be more human readable
        return True

    ## Reset the cursor position to 0 (read the file back from the beginning)
    def resetpos(self, *args, **kwargs):
        BaseParser.resetpos(self, *args, **kwargs)

    ## Set the cursor position to read the file from a specified byte
    def setpos(self, pos=0, *args, **kwargs):
        BaseParser.setpos(self, pos, *args, **kwargs)

# Some debug testing here
if __name__ == '__main__':
    import random
    import pprint # for debugging
    jsonparser = JsonParser()
    types = jsonparser.load('types.txt')
    data = jsonparser.load('data.txt', True)
    print('Data:')
    print(pprint.pformat(data))
    random.seed()
    print('SVTime for one random sample: %s' % data[random.randint(1, len(data))]['svtime']['value'])
    print
    print('Types:')
    print(pprint.pformat(types))
    print('Cheater feature type: %s' % types['cheater']['type'])
