#!/usr/bin/env python
# encoding: utf-8

## @package oacs.interactive
# Manage the interactive interface using IPython Notebook

import sys
import IPython.frontend.terminal.ipapp as ipapp
#from IPython.frontend.html.notebook import notebookapp # if you want to just import the notebook, but some commandline switches like --ipython-dir won't work

## Launch an interactive interface using IPython Notebook
#   @param  *args   a list of extra commandline switches you want to propagate to IPython Notebook
def launch_notebook(*args):
    app = ipapp.TerminalIPythonApp.instance()
    #app = notebookapp.NotebookApp.instance() # if you want to just import the notebook, but some commandline switches like --ipython-dir won't work
    allargs = ['notebook', '--pylab', 'inline', 'ipynb', '--ipython-dir', 'ipynb-profile'] # Set the minimum set of arguments necessary to launch the ipython notebook (note: --ipython-dir is necessary for windows, you need to set a local dir, else ipython might not have access to the default config folder inside Users); you can add --no-browser for daemon at startup; --notebook-dir=/home/foo/wherever to change notebook dir, or just give the directory as a parameter (it's the same)
    if args: # add optional commandline arguments if at least one is supplied (arguments not recognized by oacs will be propagated to IPython Notebook)
        allargs.extend(*args)
    app.initialize(allargs) # Initialize the IPython Notebook
    sys.exit(app.start()) # Start the IPython Notebook (will open a new page in the browser)

if __name__ == '__main__':
    launch_notebook()