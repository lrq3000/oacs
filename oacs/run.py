#!/usr/bin/env python
# encoding: utf-8

from auxlib import *
from oacs.configparser import ConfigParser
import os

class Runner:

    rootdir = 'oacs'

    def init(self, args, extras):
        #-- Loading config
        self.config = ConfigParser()
        configfile = args['config']; del args['config']
        self.config.init(configfile)
        self.config.load(args, extras)

        #-- Loading classes
        for (submod, classname) in self.config.config["classes"].iteritems(): # for each item/module specified in classes
            # if it is a list of classes, we load all the classes into a local list of classes
            if type(classname) == type(list()):
                self.__dict__[submod] = {} # initializing the local list of classes
                # for each class in the list
                for classname2 in classname:
                    # we add the class
                    self.addclass(submod, classname2, True)
            # if a special string "all" is supplied, we load all the classes into a local list of classes
            # TODO: there is a problem, because we just fetch the list of files and try to deduce the classname from the filename, but this can't work because the filename is all lowercase but not the classname! Try to find the classname from the module dictionary?
            elif classname == 'all':
                self.__dict__[submod] = {} # initializing the local list of classes
                modlist = os.listdir(os.path.join(self.rootdir, submod)) # loading the list of files/submodules
                # Trim out the base class and __init__
                if 'base' in modlist:
                    del modlist['base']
                if '__init__' in modlist:
                    del modlist['__init__']
                # For each submodule
                for classname2 in modlist:
                    # we add the class
                    self.addclass(submod, classname2, True)
            # if we just have a string, we add the class that corresponds to this string
            # Note: the format must be "submodule": "ClassName", where submodule is the folder containing the subsubmodule, and "ClassName" both the class name, and the subsubmodule filename ("classname.py")
            else:
                self.addclass(submod, classname)

        return True

    def addclass(self, submod, classname, listofclasses=False):
        try:
            aclass = import_class('.'.join([self.rootdir, submod, classname.lower()]), classname)
            if listofclasses:
                self.__dict__[submod][classname.lower()] = aclass(self.config)
            else:
                self.__dict__[submod] = aclass(self.config)
            return True
        except Exception, e:
            print("CRITICAL ERROR: importing a class failed: classname: %s package: %s\nException: %s" % (package_full, classname, str(e)))
            raise RuntimeError('Unable to import a class')

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