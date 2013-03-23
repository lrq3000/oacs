#!/usr/bin/env python

#mp_guard.py
"""tracks invocation by creating an environment variable; if that
variable exists when next called a loop is in progress"""

import os

class Brick(Exception):
    def __init__(self):
        Exception.__init__(self, "Your machine just narrowly avoided becoming"
                                 " a brick!")

if 'MP_GUARD' in os.environ:
    raise Brick

os.environ['MP_GUARD'] = 'active'