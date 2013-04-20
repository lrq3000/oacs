#!/usr/bin/env python
# encoding: utf-8

## @package csvparser
#
# A simple parser to parse the data from a file containing data in CSV format and return a Pandas structure

from oacs.inputparser.baseparser import BaseParser

import StringIO
import csv

import pandas as pd

## CsvParser
#
# A simple parser to parse the data from a file containing data in CSV format and return a Pandas structure
class CsvParser(BaseParser):
    ## @var config
    # An instance of the ConfigParser object, already loaded

    ## @var fields
    # Contain the list of features names

    ## Constructor
    # @param config An instance of the ConfigParser class
    def __init__(self, config=None, *args, **kwargs):
        self.fields = []
        return BaseParser.__init__(self, config, *args, **kwargs)

    ## Load the whole content of a file containing data in CSV format and return pandas's DataFrames
    # @param file Path to the input file to read
    def load(self, file=None, row_header=0, col_header=None, *args, **kwargs):
        # If the input file was not given in argument, we use the config
        if not file:
            file = self.config.config['datafile']

        # Read the Data file in chunks of 1000 lines (to avoid a too big memory footprint)
        datagen = pd.read_csv(file, iterator=True, chunksize=1000, index_col=col_header, header=row_header, prefix='X')
        data = pd.concat([chunk for chunk in datagen], ignore_index=True)

        # Update the list of fields names
        self.fields = data.keys

        return data

    ## Read data from a CSV file one-line-by-one and return pandas's Series (this is a generator)
    # Note: by default, the first row is thought to be the keys. If not, change row_header to None.
    # Note2: this implementation has no memory once it stops, so that you can't continue where you left last time (when you reached EOF)!
    # @param file Path to the input file to read
    def __read_alt(self, file=None, chunks_size=1, row_header=0, col_header=None, *args, **kwargs):
        # If the input file was not given in argument, we use the config
        if not file:
            file = self.config.config['datafile']

        # Check that variables values are possible
        if chunks_size < 1:
            chunks_size = 1

        # Read the Data file in chunks of 1000 lines (to avoid a too big memory footprint)
        datagen = pd.read_csv(file, iterator=True, chunksize=chunks_size, index_col=col_header, header=row_header, prefix='X')

        # Return one line (Series) of data from the generator
        for data in datagen:
            yield data.transpose()[0] # convert to a Series

    ## Read data from a CSV file one-line-by-one and return pandas's Series (this is a generator)
    # Note: by default, the first row is thought to be the keys. If not, change row_header to None.
    # @param file Path to the input file to read
    def read(self, file=None, skip_to_end=False, *args, **kwargs):
        # If the input file was not given in argument, we use the config
        if not file:
            file = self.config.config['datafile']

        # Skip to the end of the file (avoid redetecting the same samples)
        if skip_to_end and not self.getpos():
            self.setpos(pos='end', file=datafile)
            self.cursorpos = self.getpos()
        elif self.getpos() is None:
            self.setpos(0)

        # Update the fields keys if not yet done (first time we read the file)
        if not self.fields:
            with open(file, 'rb') as f:
                f.seek(0,0) # position at the absolute beginning of the file
                csvdata = csv.reader(f, delimiter = ",", skipinitialspace=True, quotechar='"')
                self.fields = csvdata.next() # read the first line of the file

        # Main loop to read the data from the file
        with open(file, 'rb') as f:
            # Set reading cursor position to the latest line not yet read
            f.seek(self.getpos(), 0)

            # try to read one line
            if not f.readline(): # nothing new to read? then return None and wait until next iteration
                return

            # Else we have new lines to read, then read on!

            # Reset cursor position
            f.seek(self.getpos(), 0)

            for line in f:

                if not line: break # if line is empty, just return None and end the generator

                linein = StringIO.StringIO(line)

                # Convert to a pandas Series
                X = pd.read_csv(linein, index_col=None, header=None)
                X = X.transpose()[0]

                # If this is the header line (with the columns names), we just skip it because we already have the columns names using the types file
                if isinstance(X[0], basestring): continue

                # Set the columns names
                X.index = self.fields

                # Return a dict with one generator (the current line as a pandas Series)
                yield {'X':X}

            # Save the latest cursor position
            self.setpos(pos=f.tell())

            return

    ## Get the current position in the file
    def getpos(self, *args, **kwargs):
        return self.cursorpos

    ## Reset the cursor position to 0 (read the file back from the beginning)
    def resetpos(self, *args, **kwargs):
        BaseParser.resetpos(self, *args, **kwargs)

    ## Set the cursor position to read the file from a specified byte
    def setpos(self, *args, **kwargs):
        BaseParser.setpos(self, *args, **kwargs)
