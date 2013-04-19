#!/usr/bin/env python
# encoding: utf-8

from auxlib import *
from oacs.configparser import ConfigParser
import os, StringIO
import pandas as pd
import time

json = import_module('ujson')
if json is None:
    json = import_module('json')
    if json is None:
        raise RuntimeError('Unable to find a json implementation')

class Runner:

    rootdir = 'oacs'

    ## @var vars contain a dynamical dict of variables used for data mining, and will be passed to every other computational function
    vars = {} # we create a reference at startup so that this dict can be passed as a reference to children objects

    ## Initialize a runner object, with all constructs necessary to use the algorithms and process data according to the provided configuration file and commandline arguments
    # @param args recognized and processed commandline arguments
    # @param extras extra commandline arguments that are not explicitly recognized (but will nevertheless be appended to the config file, so that you can overwrite pretty much any configuration parameter you want at commandline)
    def init(self, args, extras):
        self.vars = dict()
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
                # Remove all base modules (modules whose names starts with 'base')
                [modlist.remove(mod) for mod in modlist if mod.startswith('base')]
                # Remove all __init__ modules (these are only used by the python interpreter)
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
                self.__dict__[submod][classname.lower()] = aclass(config=self.config, parent=self)
            else:
                self.__dict__[submod] = aclass(config=self.config, parent=self)
            return True
        except Exception, e:
            package_full = '.'.join([self.rootdir, submod, classname.lower()])
            print("CRITICAL ERROR: importing a class failed: classname: %s package: %s\nException: %s" % (package_full, classname, str(e)))
            raise RuntimeError('Unable to import a class')

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
            if self.vars.get("lastout", None): del self.vars["lastout"]
            # Save this output
            self.vars.update({"lastout": dictofvars})

    ## Generically call one object and its method (if obj is a list, it will call the method of each and every one of the modules in the list)
    # @param obj Object or list of objects
    # @param method Method to call in the object(s) (as string)
    # @param args Optional arguments to pass to the method
    def generic_call(self, obj, method, args=None):
        if args is None:
            args = {}
        # If we have a list of modules to call, we call the method of each and every one of those modules
        if type(obj) == type(dict()):
            # For every module in the list
            for submodule in obj.itervalues():
                # Get the callable object's method
                fullfunc = getattr(submodule, method)
                # Call the specified function for the specified module
                self.updatevars(fullfunc(**args.update(self.vars)))
        # Else if it is an object, we directly call its method
        else:
            # Get the callable object's method
            fullfunc = getattr(obj, method)
            # Call the specified function for the specified module
            self.updatevars(fullfunc(**self.vars))

    ## Generically call any module given a list of dicts containing {"submodule name": "method of the class to call"}
    # @param executelist A list containing the sequence of modules to launch (Note: the order of the contained elements matters!)
    def execute(self, executelist):
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

                    self.generic_call(self.__dict__[module], func)
                    #self.updatevars(self.learningalgo.learn(**self.vars))
                    # dans learningalgo faire un if self.config.config['bigdata'] self.learn_bulk() or self.learn_bigdata()
                    #eg: return {'X': df, 'Y': something, etc..}
            except Exception, e:
                print str(e)

        return True

    ## Write down the parameters into a file
    # Format of the file: json structure consisting of a dict where the keys are the names of the vars, and the values are strings encoding the data in csv format
    # TODO: replace by pandas.to_json() when the feature will be put back in the main branch?
    @staticmethod
    def save_vars(jsonfile, dictofvars, exclude=None):
        finaldict = dict()

        # For each object in our dict of variables
        for key, item in dictofvars.iteritems():
            # If this variable is in the exclude list, we skip it
            if exclude and key in exclude:
                continue
            # Try to save the pandas object as CSV
            try:
                out = StringIO.StringIO()
                item.to_csv(out)
                finaldict[key] = out.getvalue()
            # Else if it is not a pandas object, we save as-is
            except Exception, e:
                finaldict[key] = item
                print(e)

        # Save the dict of csv data as a JSON file
        try:
            f = open(jsonfile, 'wb') # open in binary mode to avoid line returns translation (else the reading will be flawed!). We have to do it both at saving and at reading.
            f.write( json.dumps(finaldict, sort_keys=True, indent=4) ) # write the file as a json serialized string, but beautified to be more human readable
            f.close()
            return True
        except Exception, e:
            print e
            return False

    ## Load the parameters from a file
    # Format of the file: json structure consisting of a dict where the keys are the names of the vars, and the values are strings encoding the data in csv format
    # TODO: replace by pandas.from_json() when the feature will be put back in the main branch?
    @staticmethod
    def load_vars(jsonfile):
        dictofvars = dict()
        # Open the file
        with open(jsonfile, 'rb') as f:
            filecontent = f.read()
        # Load the json tree
        jsontree = json.loads(filecontent)

        # For each item in the json
        for key, item in jsontree.iteritems():

            # Try to load a pandas object (Series or DataFrame)
            try:
                buf = StringIO.StringIO(item)
                df = pd.read_csv(buf, index_col=0, header=0) # by default, load as a DataFrame
                # if in fact it's a Series (a vector), we reload as a Series
                # TODO: replace all this by pd.read_csv(buf, squeeze=True) when squeeze will work!
                if df.shape[1] == 1:
                    buf.seek(0)
                    dictofvars[key] = pd.Series.from_csv(buf)

                    # Failsafe: in case we tried to load a Series but it didn't work well (pandas will failsafe and return the original string), we finally set as a DataFrame
                    if (type(dictofvars[key]) != type(pd.Series()) and type(dictofvars[key]) != type(pd.DataFrame()) or dictofvars[key].dtype == object ): # if it's neither a Series nor DataFrame, we expect the item to be a DataFrame and not a Series
                        dictofvars[key] = df

                # Else if it is really a DataFrame, we set it as DataFrame
                else:
                    dictofvars[key] = df

            # If it didn't work well, we load the object as-is
            except Exception, e:
                dictofvars[key] = item
                print(e)

        # Return the list of variables/parameters
        return dictofvars

    ## Train the system to learn how to detect cheating
    def learn(self, executelist=None):
        # We can pass an execution list either as an argument (used for recursion) or in the configuration
        if not executelist:
            executelist = self.config.config.get('run_learn', None)

        # Standard learning routine
        # If no routine is given, then we execute the standard learning routine
        if not executelist:
            executelist = []
            if self.__dict__.get('preoptimization', None):
                executelist.append({"preoptimization": "optimize"})
            executelist.append({"classifier": "learn"})
            if self.__dict__.get('postoptimization', None):
                executelist.append({"postoptimization": "optimize"})

        # Load the data prior to the execution of the learning routine
        if not self.config.config.get('bigdata'):
            self.generic_call(self.inputparser, 'load')
        else: # Special case: for the input parser, we call the read method if we are in bigdata mode
            self.updatevars({'X': self.inputparser.read()}) # we put the generator of variables in X

        # Execute all modules of the routine (either of config['run_learn'] or the standard routine)
        self.execute(executelist)

        # End of learning, we save the parameters if a parametersfile was specified
        if self.config.config.get('parametersfile', None):
            Runner.save_vars(self.config.config['parametersfile'], self.vars, ['X', 'Y']) # save all vars but X and Y (which may be VERY big and aren't parameters anyway)

        return True

    ## Main/Prediction loop
    def run(self, executelist=None):
        # Load the parameters if a file is specified
        if self.config.config.get('parametersfile', None):
            self.updatevars(Runner.load_vars(self.config.config['parametersfile']))

        # We can pass an execution list either as an argument (used for recursion) or in the configuration
        if not executelist:
            executelist = self.config.config.get('run', None)

        # Standard detection routine
        # If no routine is given, then we execute the standard detection routine
        if not executelist:
            executelist = []
            if self.__dict__.get('postoptimization', None):
                executelist.append({"postoptimization": "optimize"})
            executelist.append({"classifier": "predict"})
            executelist.append({"detector": "detect"})
            if self.__dict__.get('postaction', None):
                executelist.append({"postaction": "action"})

        # Caching a few vars (faster than accessing methods)
        run_minisleep = self.config.config.get('run_minisleep', 0.01)
        run_sleep = self.config.config.get('run_sleep', 1)

        # Main loop
        while 1:
            # Set the reading cursor at the end of the file (last line)
            skip_to_end = True
            if not self.config.config.get('simulatedetection', None):
                skip_to_end=False
            # Get the samples generator
            gen = self.inputparser.read(skip_to_end=True)
            # For each samples in the generator
            for dictofvars in gen:
                # No new lines yet? We just wait for the next iteration after having slept a bit
                if dictofvars is None: break
                # Add them to the global list of variables
                self.updatevars(dictofvars)
                # Execute all modules of the routine (either of config['run'] or the standard routine)
                self.execute(executelist)
                # Sleep a bit between each sample to give the hand to other processes
                time.sleep(run_minisleep)
            # Sleep a bit between each batch of new samples (here we finished the last batch and reached the end of file, wait a bit because anyway there won't be any new sample ASAP)
            time.sleep(run_sleep)

        return True

if __name__ == '__main__':
    runner = Runner()
    runner.init()
    runner.run()