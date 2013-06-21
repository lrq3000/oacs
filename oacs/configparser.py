#!/usr/bin/env python
# encoding: utf-8

from auxlib import *

json = import_module('ujson')
if json is None:
    json = import_module('json')
    if json is None:
        raise RuntimeError('Unable to find a json implementation')

## ConfigParser
#
# Configuration parser, will parse and load in memory the configuration and commandline switches
class ConfigParser(object):

    # Configuration file path
    configfile = 'config.json'

    # Configuration parameters tree (will be referenced by almost all other objects across the whole application)
    config = []

    ## Constructor
    def __init__(self, *args, **kwargs):
        return object.__init__(self, *args, **kwargs)

    ## Initialize the ConfigParser object by checking that the configuration file exists
    # @param configfile Path to the configuration file (must exists or else the application will crash!)
    def init(self, configfile=None, *args, **kwargs):
        if configfile:
            try:
                with open(configfile): pass # check that the file exists
                self.configfile = configfile
            except IOError, e:
                print "Can't open the specified configuration file %s, error: %s" % (configfile, str(e))
                return

    ## Load a configuration file into the local dict
    # @param pargs Recognized (processed) commandline arguments (this will overwrite parameters from the configuration file in case of conflicts)
    # @param extras Unrecognized (unprocessed) commandline arguments (will also overwrite parameters from the configuration file)
    def load(self, pargs=None, extras=None, *args, **kwargs):
        # Loading the configuration file
        with file(self.configfile) as f:
            self.config = json.loads(f.read())

        # Overwriting with recognized commandline switches
        if pargs:
            for key, value in pargs.iteritems():
                # only add the argument in config if the argument has a value (not False nor None) and this key is not already defined in the config (so an argument can only overwrite config if defined)
                if not (self.config.has_key(key) and not value):
                    self.config[key] = value

        # Overwriting with extras commandline switches
        if extras:
            i = 0
            while i < len(extras):
                key = extras[i]
                # Check if the argument accepts a value
                if '--' in key and i+1 < len(extras) and not '--' in extras[i+1]: # if the argument begins with --, and there is an argument after this one, and the next argument is in fact a value (does not begin with --), we store it with the value
                    self.config[key.lstrip('-')] = extras[i+1]
                    i += 1 # skip the next argument (which we used as a value)
                # Else this argument has no value, we just set it to True
                else:
                    self.config[key.lstrip('-')] = True
                i += 1

    ## Reload the configuration file
    def reload(self, *args, **kwargs):
        self.load()

    ## Save the current configuration (with commandline arguments processed) into a file
    # @param file Path to where the configuration file should be saved
    def save(self, file, *args, **kwargs):
        with open(file, 'wb') as f: # open in binary mode to avoid line returns translation (else the reading will be flawed!). We have to do it both at saving and at reading.
            f.write( json.dumps(self.config, sort_keys=True, indent=4) ) # write the config as a json serialized string, but beautified to be more human readable
        return True

    # Get a value from the config dict (this is a proxy method)
    def get(self, *args, **kwargs):
        return self.config.get(*args, **kwargs)

    # Set a value in the config dict (this is a proxy method)
    def set(self, *args, **kwargs):
        return self.config.set(*args, **kwargs)
