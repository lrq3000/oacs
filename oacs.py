#!/usr/bin/env python
# encoding: utf-8

__author__  = 'lrq3000'
__version__ = '1.0.0'


import sys
if sys.version_info >= (3,):
    raise SystemExit("Sorry, cannot continue, this application is not yet compatible with python version 3! (or try using python 2to3 utility)")
if sys.version_info < (2,6):
    raise SystemExit("Sorry, cannot continue, this application is not compatible with python versions earlier than 2.6!")

import oacs.main

## Main entry point for the OACS program
# @param argv A list of strings containing the arguments (optional)
def main(argv=None):
    oacs.main.main(argv)

if __name__ == '__main__':
    sys.exit(main())