## @mainpage OACS developer's documentation
#  @section intro_sec Introduction
#  OACS (Open Anti-Cheat System) is an opensource server-side anti-cheat system.
#
# The main purpose of this project is to be:
# - Server-side: no way to tamper the data since all the processing is done from the server, not from the clients. It is also more efficient since the server has generally more resources.
# - Open and shareable: you can share your results with other servers' administrators and together converge to better results.
# - KISS: the software is simple to use, simple to configure to your needs, and simple to extend with a clear and concise codebase.
# - Modular: if you need to add a new algorithm or a new postaction, you can simply code a module. The rest of the software will work flawlessly and use your module.
# - Reusable and generic: most of the modules are reusable for any game or purpose.
# - Low port overhead: you need only to code an interface between the game's data and OACS, all the rest is already done and working.
#
# @section overview_sec Overview
#
# The system is split across a few main base modules that are necessary for functionning and cannot be replaced, which are all the scripts placed at the root of the oacs subfolder, mainly:
# - run.py which is the main Runner script (will run everything neatly given a configuration file and output the results). This is the main manager script. It also manages the global namespace of variables and modules. This is the "glue" of all the modules.
# - main.py which is the commandline entry point of the program and will launch the desired functionalities.
# - configparser.py which contains ConfigParser and manage all the configuration. This object is instanciated by Runner and then referenced inside all modules thank's to Base class, so that any module can access the whole configuration file at any moment (and thus declare very simply its very own configuration parameters).
# - base.py which is the base class that all classes/modules must inherit from to get the basic functionnalities like access to the config file and parent class. However, you will generally prefer to inherit from the specific base class of your type of module (eg: basepostaction/basepostaction.py)
#
# Apart from these base modules, all the other modules are split across subfolders, which represent the type of functionality they implement. Currently these types are available:
# - classifier: algorithms that will learn the parameters and predict/detect anomalies (prediction must be a number between 0 and 1)
# - cost
# - decider: based on a classifier's prediction, decide whether a prediction's value is anomalous (based on some kind of threshold or decision algorithm)
# - inputparser: read and parse the data files (from which the classifier will learn) into neat Pandas object.
# - lib: not really modules, this folder contains auxiliary libraries (eg: debug, argparse).
# - postaction: process actions after a detection occurred.
# - postoptimization: optimizations of the parameters after the learning process (eg: prediction threshold detection, cross validation).
# - preoptimization: optimizations of the data that will always be applied before the learning process or detection process (eg: features normalization/scaling).
#
# Then inside these folders you will find the modules, which all share the same public entry points (same public methods, thus the access is the same but the functionality provided varies per module).
#
# One thing you need to know is that you can specify completely how you want the program to run, and what algorithms to use, and in which order, directly in the configuration file (see below the related chapter for more infos).
#
# An important note is about the configuration file and commandline arguments: they are all shared and accessible to all modules, and are considerated the same (except that commandline arguments have precedence over configuration file).
# This mean that you can use any configuration parameter as a commandline argument, and vice versa (except for the configuration file location: you need to specify it at commandline).
#
# Another important note is about the variables management: all the variables returned by modules are stored in a kind of protected namespace, which is a global namespace inside Runner.
# Indeed, all variables are accessible inside runner.vars (eg: runner.vars['X']), and will be propagated to all other modules and methods.
#
# @section createkindmodule_sec Create your own kind of module
#
# It is very easily possible to create a new kind of module: all you need to do is:
# - create a new subfolder inside "oacs", eg "newkind".
# - create an __init__.py file at the root of the folder "newkind" (you can leave it empty or just put a #, it's just used for Python to recognize your new folder as a Python submodule).
# - create a base class with the name "base" + name of the subfolder (eg: "basenewkind.py") and create a new class inside with the same name as the python file (eg: "BaseNewKind") and inherit from BaseClass (oacs/base.py). To get done with this quicker and more easily, you can copy the base class from another module and just change to the appropriate names.
# - define 1 or 2 public generic methods that will be accessed for learning, and the second one for prediction (some modules do need only one public access, like postaction which only requires the method "action"). This is necessary for the software to be generic, thus modules need to implement public and generic entry points that provide the same "broad concept functionality".
#
# Then in these modules folders, will find several modules, each with a different name and purpose.
#
# @section createmodule_sec Create your own module
#
# If you want to create your own module, you simply have to:
# - make a new python file in the appropriate subfolder (eg: "newkind/mynewmodule.py")
# - create, inside this file, a class with the same name (but not necessarily the same case, eg: "class MyNewMODULE")
# - you must then implement in your class at least the public generic methods that the base class implements.
#
# @section configuration_sec Configuration
#
# OACS main modules provide a few main configuration parameters, but then each module can specify its own.
#
# Please refer to the documentation of the module if you want to know more about the configuration parameters you can use.
#
# Here is a non-exhaustive list of OACS main configuration parameters:
# - run: routine to be used at detection (list of modules and their methods to call) - order matters!
# - run_learn: routine to be used at learning (list of modules and their methods to call) - order matters!
# - classes: list of modules to load (Note that you can load more classes and not use them in run or run_learn! They will be then preloaded and available for manual introspection and usage).
# - datafile: input data file from which to learn the parameters
# - typesfile: auxiliary file for the data file
# - parametersfile: where the parameters will be saved at learning, and loaded at detection
# - playerstable: the table of players association with the datafile
#
# @section variables_sec Variables management
#
# At some point of the project, one of the biggest problem was: how to return variables in a way that they are generically handled and passed to the correct methods and modules that needs them, but with keeping clear methods declaration (ie: which variables are required by a method) and without having a too big overhead on the methods nor in memory (ie: no duplication).
#
# The solution adopted was to use a global, private namespace managed by Runner (in runner.vars) and shared by reference to all submodules.
#
# In fact, to be totally precise, submodules don't get a reference to the global variables manager: variables are unpacked when calling the methods of the submodules. This has a triple advantage: first it keeps the genericity that was wanted, secondly it forces to use keyword arguments and thus the classes become inheritables, thirdly and foremost it allows to keep clear definitions of the variables required by the methods (eg: mymethod(X=None, Y=None, *args, **kwargs)), and thus even with the genericity, the methods still stay faithful to the python idiomatic of keeping things clear.
#
# However, this requires that submodules methods return a dict of vars, and not just a variable alone nor a list. Other kind of objects than dict of vars will be stored but temporarily in a placehold (runner.vars['lastout1]), because there is no label to assign them to and to propagate to other modules. But this is a meager payback for this simple and elegant implementation.
#
#
# @section interactive_sec Interactive GUI
#
# You can load and use OACS in a IPython Notebook GUI.
#
# All you need to do is install a recent IPython release (which contains notebooks), and launch OACS with these arguments:
#
# python oacs.py --interactive
#
# A webpage should open in your browser and you can then use one of the notebooks to run OACS just by clicking, everything is done for you.
#
# The main interest for this GUI is foremost to test the datas or results or to develop your own algorithms directly in this GUI, and then porting the code to your own module once it's working (that's what I did for most modules). Example codes are offered to help you.
#
# @section advices_sec Advices and guidelines
# - This project rely heavily on Pandas and Numpy, and it is advised that you use Pandas objects whenever possible.
# - Always inherit from the base class of your kind of module (eg: basepostaction.py).
# - For public methods (that will be accessed from outside or by Runner), ALWAYS use keywords arguments + variable positional and keyword arguments.
# Eg:
#
# def mymethod(X, Y): # this is not good at all, it won't work
#   pass
#
# def mymethod(X=None, Y=None, *args, **kwargs): # this will work and will be inheritable and overloadable
#   pass
#
# - If you want your returned values to be memorized in the Runner's global namespace (thus accessible to other modules) and saved in the parameters file, return your variables in a dictionary.
# Eg:
#
# return myvalue # won't work, the value will not be stored nor accessible to other modules
#
# return {'Myvalue': myvalue} # This will be stored and accessible in runner.vars['Myvalue']
#
#
#  @section license_sec License
# This program is free software; you can redistribute it and/or modify
# it under the terms of the Affero GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the Affero GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
#
# A full copy of the license is available at: http://www.gnu.org/licenses/agpl-3.0.txt
#