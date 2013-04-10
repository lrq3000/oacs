#!/usr/bin/env python
# encoding: utf-8

## @package baseparser
#
# This contains the base parser class to be used as a template for other parsers

from oacs.base import BaseClass
import os

## BaseParser
#
# Base input parser, use this as a template for your input parser
class BaseParser(BaseClass):

    ## @var config
    # An instance of the ConfigParser object, already loaded

    ## @var cursorpos
    # Last seeking position that we read from the input file (used to continue reading from the same position)

    ## Constructor
    # @param config An instance of the ConfigParser class
    def __init__(self, config, *args, **kwargs):
        return BaseClass.__init__(self, config, *args, **kwargs)

    ## Load the whole content of a file and return it
    # @param file Path to the input file to read (optional)
    def load(self, file=None, *args, **kwargs):
        # If the input file was not specified, we use the config
        if not file:
            file = self.config.config["inputfile"]

        try:
            f = open(file, 'rb') # open in binary mode to avoid line returns translation (else the reading will be flawed!). We have to do it both at saving and at reading.
            content = f.read()
            self.cursorpos = f.tell()
        except Exception, e:
            print str(e)
            return False
        finally:
            f.close()
        return content

    ## Read a file one line by one line (generator)
    # @param file Path to the input file to read (optional)
    def read(self, file=None, *args, **kwargs):
        # If the input file was not specified, we use the config
        if not file:
            file = self.config.config["inputfile"]

        if not hasattr(self, 'cursorpos'):
            self.cursorpos = 0

        # open in binary mode to avoid line returns translation (else the reading will be flawed!). We have to do it both at saving and at reading.
        with open(file, 'rb') as f:
            # Getting the stats of the game log (we are looking for the size)
            filestats = os.fstat(f.fileno())
            # Compare the current cursor position against the current file size,
            # if the cursor is at a number higher than the game log size, then
            # there's a problem
            if self.cursorpos > filestats.st_size:
                print('%s: Input file is suddenly smaller than it was before (%s bytes, now %s), the file was probably either rotated or emptied. The application will now re-adjust to the new size of the file (read back from the beginning).' % (self.__class__.__name__, str(f.tell()), str(filestats.st_size)) )
                f.seek(0, os.SEEK_END)
                self.resetpos()
            # Else we continue where we were reading the last time we opened the file
            else:
                f.seek(self.cursorpos, 0) # absolute seeking: position to the beginning of the row

            # Read all lines until there are no more
            for line in f:
                yield line

            # store the last cursor position (for the next time we will open the file again, so that we can continue at the same position)
            self.cursorpos = f.tell()

    ## Reset the cursor position to 0 (read the file back from the beginning)
    def resetpos(self, *args, **kwargs):
        self.cursorpos = 0

    ## Set the cursor position to read the file from a specified byte
    def setpos(self, pos=None, *args, **kwargs):
        if pos >= 0:
            self.cursorpos = pos
