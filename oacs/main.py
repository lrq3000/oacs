#!/usr/bin/env python
# encoding: utf-8

import argparse
import sys

import oacs.run
import interactive

def parse_cmdline_args(argv=None):
    if argv is None:
        argv = sys.argv[1:]

    desc = '''Open Anti Cheat System (OACS) ---
    Description: Server-side anti-cheat system for online games.
    '''
    epi = '''Note: commandline switches have precedence over configuration file. This also means that you can use absolutely any parameter that is valid in a configuration file, as a commandline argument.'''

    #-- Constructing the parser
    parser = argparse.ArgumentParser(description=desc,
                                     add_help=True, argument_default=argparse.SUPPRESS, conflict_handler="resolve",
                                     epilog=epi)

    #-- Getting the arguments
    parser.add_argument('--help', '-help', '-h', dest='help', action='store_true', default=False,
                        help='show this help message and exit')
    parser.add_argument('--interactive', '-i', dest='interactive', action='store_true', default=False,
                        help='interactive mode, open an ipython notebook web interface (you need ipython notebook to be installed)')
    parser.add_argument('--norun', '-n', dest='norun', action='store_true', default=False,
                        help='do not run the main loop, only load the constructs and config file, and then let you use these constructs in whatever way you want using Python or Notebook.')
    parser.add_argument('--config', '-c', dest='config', action='store', default=None,
                        help='specify a path to a specific configuration file you want to use')



    #-- Parsing (loading) the arguments
    try:
        [args, extras] = parser.parse_known_args(argv) # Storing all arguments into args, and remaining unprocessed (unrecognized) arguments by oacs will be propagated to other applications (eg: IPython Notebook)
        #extras.insert(0, sys.argv[0]) # add the path to this script file (to normalize the arguments)
        #sys.argv = extras # replace the system arguments by only the remaining unprocessed ones. This will produce a bug with ipython notebook
    except BaseException, e: # in case of an exception at parsing arguments, try to continue
        print('Exception: %s' % str(e)) # print the exception anyway
        pass

    return (args, extras, parser)

def main(argv=None):
    #-- Parsing (loading) the arguments
    [args, extras, parser] = parse_cmdline_args(argv)
    args = args.__dict__ # convert to an array (so that it becomes iterable)

    #-- Processing the commandline switches
    # Help message
    if args['help']:
        parser.print_help()
        return
    # Interactive mode, we launch the IPython Notebook
    elif args['interactive']:
        interactive.launch_notebook(extras)
    # Scripting mode: load the config and make the constructs, but do not run the main loop
    elif args['norun']:
        oacs.run.init(args, extras)
    # Run the main OACS loop by default
    else:
        oacs.run.init(args, extras)
        oacs.run.run()

if __name__ == '__main__':
    main()
