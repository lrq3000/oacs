#!/usr/bin/env python
# encoding: utf-8

from oacs.configparser import ConfigParser

def init(args, extras):
    config = ConfigParser()
    configfile = args['config']; del args['config']
    config.init(configfile)
    config.load(args, extras)

    return True

# main loop
def run():
    oacs.configparser
    oacs.learn
    while 1:
        oacs.inputparser # ou plutot on charge d'abord le input parser, et apres on fait InputParser.read()
        oacs.predict

    return True

if __name__ == '__main__':
    init()
    run()