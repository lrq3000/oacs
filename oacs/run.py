#!/usr/bin/env python
# encoding: utf-8

from oacs.configparser import ConfigParser

class Runner:


    def init(self, args, extras):
        self.config = ConfigParser()
        configfile = args['config']; del args['config']
        self.config.init(configfile)
        self.config.load(args, extras)

        return True

    # main loop
    def run(self):
        oacs.configparser
        oacs.learn
        while 1:
            oacs.inputparser # ou plutot on charge d'abord le input parser, et apres on fait InputParser.read()
            oacs.predict

        return True

if __name__ == '__main__':
    runner = Runner()
    runner.init()
    runner.run()