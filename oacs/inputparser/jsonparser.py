#!/usr/bin/env python
# encoding: utf-8

## @package jsonparser
#
# General purpose JSON parser

from oacs.inputparser.base import BaseParser

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
    def __init__(self, config, *args, **kwargs):
        return BaseParser.__init__(self, config, *args, **kwargs)

    ## Load the content of a file as JSON and return a Python object corresponding to the JSON tree
    # @param file Path to the input file to read
    def load(self, file, addrootarray=False, *args, **kwargs):
        try:
            f = open(file, 'rb') # open in binary mode to avoid line returns translation (else the reading will be flawed!). We have to do it both at saving and at reading.
            if (addrootarray):
                jsonraw = f.read()
                jsonraw = os.linesep.join([s for s in jsonraw.splitlines() if s]) # remove empty lines
                jsonraw = reg.sub(r'\1,', jsonraw) # add the missing commas between the objects in the root array
                jsonraw = jsonraw.rstrip(',') # remove the last comma
                jsonraw = "[%s]" % jsonraw # convert to a json array of json objects (just by enclosing in [])
            else:
                jsonraw = f.read()
            jsoncontent = json.loads( jsonraw )
            f.close()
            return jsoncontent
        except Exception, e:
            print e
            return False

    def save(self, jsoncontent, jsonfile, *args, **kwargs):
        try:
            f = open(jsonfile, 'wb') # open in binary mode to avoid line returns translation (else the reading will be flawed!). We have to do it both at saving and at reading.
            f.write( json.dumps(jsoncontent, sort_keys=True, indent=4) ) # write the file as a json serialized string, but beautified to be more human readable
            f.close()
            return True
        except Exception, e:
            print e
            return False

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
