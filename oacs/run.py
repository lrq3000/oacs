#!/usr/bin/env python
# encoding: utf-8

from auxlib import *
from oacs.configparser import ConfigParser
import os

class Runner:

    rootdir = 'oacs'

    ## @var vars contain a dynamical dict of variables used for data mining, and will be passed to every other computational function
    vars = {} # we create a reference at startup so that this dict can be passed as a reference to children objects

    ## Initialize a runner object, with all constructs necessary to use the algorithms and process data according to the provided configuration file and commandline arguments
    # @param args recognized and processed commandline arguments
    # @param extras extra commandline arguments that are not explicitly recognized (but will nevertheless be appended to the config file, so that you can overwrite pretty much any configuration parameter you want at commandline)
    def init(self, args, extras):
        #-- Loading config
        self.config = ConfigParser()
        configfile = args['config']; del args['config'] # delete the config argument, which is at best a self reference
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
            # if a special string "all" is supplied, we load all the classes into a local list of classes (if a class with a similar name to the filename exists - the classname can have mixed case, the case doesn't matter if the filename corresponds to the classname.lower())
            elif classname == 'all':
                self.__dict__[submod] = {} # initializing the local list of classes
                modlist = os.listdir(os.path.join(self.rootdir, submod)) # loading the list of files/submodules
                modlist = list(set([os.path.splitext(mod)[0] for mod in modlist])) # strip out the extension + get only unique values (else we will get .py and .pyc filenames, which are in fact the same module)
                # Trim out the base class and __init__
                if 'base' in modlist:
                    modlist.remove('base')
                if '__init__' in modlist:
                    modlist.remove('__init__')

                # For each submodule
                for classname2 in modlist:
                    full_package = '.'.join([self.rootdir, submod, classname2.lower()])
                    mod = import_module(full_package) # we need to load the package before being able to list the classes contained inside
                    # We list all objects contained in this module (normally we expect only one class, but nevermind)
                    for iclass, iclassname in [(obj, obj.__name__) for obj in [getattr(mod, name) for name in dir(mod)] if isinstance(obj, type)]:
                        # If the object is a class, and the class name is the same as the filename, we add an instance of this class!
                        if iclassname.lower() == classname2.lower():
                            # we add the class
                            self.addclass(submod, iclassname, True)
            # if we just have a string, we add the class that corresponds to this string
            # Note: the format must be "submodule": "ClassName", where submodule is the folder containing the subsubmodule, and "ClassName" both the class name, and the subsubmodule filename ("classname.py")
            else:
                self.addclass(submod, classname)

        return True

    ## Instanciate dynamically a class and add it to the local dict
    # @param submod name of the subfolder/submodule where the subsubmodule resides
    # @param classname both the subsubmodule filename (eg: classname.py) and the class name (eg: ClassName)
    # @param listofclasses if True, instanciate this class in a list of classes, instead of just directly a property of the current object (eg: instead of self.inputparser, you will get: self.inputparser["firstparser"], self.inputparser["secondparser"], etc...)
    def addclass(self, submod, classname, listofclasses=False):
        try:
            aclass = import_class('.'.join([self.rootdir, submod, classname.lower()]), classname)
            if listofclasses:
                self.__dict__[submod][classname.lower()] = aclass(self.config)
            else:
                self.__dict__[submod] = aclass(self.config)
            return True
        except Exception, e:
            package_full = '.'.join([self.rootdir, submod, classname.lower()])
            print("CRITICAL ERROR: importing a class failed: classname: %s package: %s\nException: %s" % (package_full, classname, str(e)))
            raise RuntimeError('Unable to import a class')

    ## Generically call any submodule given a list of dicts containing {"submodule name": "method of the class to call"}
    # @param executelist A list containing the sequence of modules to launch (Note: the order of the contained elements matters!)
    def generic_call(self, executelist):
        # Loop through all modules in run_learn list
        for mod in executelist:
            # Catch exceptions: if a module fails, we continue onto the next one
            try:
                # Special case: this is a sublist, we run all the modules in the list in parallel
                if type(mod) == type(list()):
                    self.generic_call(mod) # TODO: launch each submodule in parallel (using subprocess or threading, but be careful: Python's threads aren't efficient so this is not useful at all, and subprocess creates a new object, so how to communicate the computed/returned variables efficiently in memory?)
                else:
                    # Unpacking the dict
                    module = mod.keys()[0]
                    func = mod.values()[0]
                    # Get the class method
                    fullfunc = getattr(self.__dict__[module], func)
                    # Call the specified function for the specified module
                    self.updatevars(fullfunc(**self.vars))
                    #self.updatevars(self.learningalgo.learn(**self.vars))
                    # dans learningalgo faire un if self.config.config['bigdata'] self.learn_bulk() or self.learn_bigdata()
                    #eg: return {'X': df, 'Y': something, etc..}
            except Exception, e:
                print str(e)

        return True

    ## Train the system to learn how to detect cheating
    def learn(self, executelist=None):
        # We can pass an execution list either as an argument (used for recursion) or in the configuration
        if not executelist:
            executelist = self.config.config.get('run_learn', None)

        # Execute all modules of run_learn
        if executelist:
            self.generic_call(executelist)

        # Else we execute the standard learning routine
        else:
            # Special case: for the input parser, we call the read method if we are in bigdata mode
            if not self.config.config.get('bigdata'):
                self.updatevars(self.inputparser.load())
            else:
                self.updatevars(self.inputparser.read())

        return True

    ## Update the local dict vars of variables
    #
    # This function is used as a proxy to accept any arbitrary number of returned arguments from functions, and will store them locally, and then the vars dict will be passed onto other children objects
    def updatevars(self, dictofvars):
        # Create the local vars dict if it does not exist
        if not hasattr(self, 'vars'):
            self.vars = {}
        # Update/add the values inside dictofvars (if it is a dictionary of variables)
        if type(dictofvars) == type(dict()):
            self.vars.update(dictofvars) # add new variables from dict and merge updated values for already existing variables
        # Else, it may be a list or an object or just a scalar (this means the function is not conforming to the dev standards), then can't know where to put those results and we just memorize them inside a "lastout" entry as-is.
        else:
            # Delete the previous output
            if self.vars["lastout"]: del self.vars["lastout"]
            # Save this output
            self.vars.update({"lastout": dictofvars})

    ## Main/Prediction loop
    def run(self, executelist=None):
        # We can pass an execution list either as an argument (used for recursion) or in the configuration
        if not executelist:
            executelist = self.config.config.get('run', None)

        # Execute all modules of run_learn
        if executelist:
            self.generic_call(executelist)

        # Else we execute the standard learning routine
        else:
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