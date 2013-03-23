#!/usr/bin/env python
# encoding: utf-8

from auxlib import *

json = import_module('ujson')
if json is None:
    json = import_module('json')
    if json is None:
        raise RuntimeError('Unable to find a json implementation')

class ConfigParser(object):
    configfile = 'config.json'
    config = []

    def __init__(self, *args, **kwargs):
        return object.__init__(self, *args, **kwargs)

    def init(self, configfile=None, *args, **kwargs):
        if configfile:
            try:
                with open(configfile): pass # check that the file exists
                self.configfile = configfile
            except IOError, e:
                print "Can't open the specified configuration file %s, error: %s" % (configfile, str(e))
                return

    def load(self, pargs=None, extras=None, *args, **kwargs):
        # Loading the configuration file
        with file(self.configfile) as f:
            self.config = json.loads(f.read())

        # Overwriting with recognized commandline switches
        if pargs:
            for key, value in pargs.iteritems():
                self.config[key] = value

        # Overwriting with extras commandline switches
        if extras:
            keymem = None # store the key in case this is an argument that accepts a value
            for key in extras.itervalues():
                # Storing an argument accepting a value (here it's the 2nd iteration, we already detected the key and now we process the value)
                if keymem:
                    self.config[keymem] = key
                    keymem = None
                # If this argument accepts a value (starts with --), we memorize the key and we will store this argument at the next iteration
                elif '--' in key:
                    keymem = key
                # Else this is a simple argument, we just store it
                else:
                    self.config[key.lstrip('-')] = True
