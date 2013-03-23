#!/usr/bin/env python

import sys, exceptions

def import_module(module_name):
    ''' Reliable import, courtesy of Armin Ronacher '''
    try:
        __import__(module_name)
    except ImportError:
        exc_type, exc_value, tb_root = sys.exc_info()
        tb = tb_root
        while tb is not None:
            if tb.tb_frame.f_globals.get('__name__') == module_name:
                raise exc_type, exc_value, tb_root
            tb = tb.tb_next
        return None
    return sys.modules[module_name]

def str2int(s):
    ''' Convert a string to int '''
    try:
        return int(s)
    except exceptions.ValueError:
        return int(float(s))
