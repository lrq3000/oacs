#!/usr/bin/env python
# encoding: utf-8

## @package csvparser
#
# A simple parser to parse the data from a file containing data in CSV format and return a Pandas structure

from oacs.inputparser.baseparser import BaseParser

from oacs.auxlib import *
import os
import itertools

import pandas as pd

## CsvParser
#
# A simple parser to parse the data from a file containing data in CSV format and return a Pandas structure
class CsvParser(BaseParser):
    ## @var config
    # An instance of the ConfigParser object, already loaded

    ## @var types
    # Contain the list of features names and their types (as int, because in the game interface we use an int enum)

    ## Constructor
    # @param config An instance of the ConfigParser class
    def __init__(self, config, *args, **kwargs):
        return BaseParser.__init__(self, config, *args, **kwargs)

    ## Load the whole content of a file containing data in CSV format and return pandas's DataFrames
    # @param file Path to the input file to read
    def load(self, file=None, *args, **kwargs):
        # If the input file was not given in argument, we use the config
        if not file:
            file = self.config.config['datafile']

        # Read the Data file in chunks of 1000 lines (to avoid a too big memory footprint)
        datagen = pd.read_csv(file, iterator=True, chunksize=1000, index_col=None, header=None, prefix='X')
        data = pd.concat([chunk for chunk in datagen], ignore_index=True)

        return data

    ## Read data from a CSV file one-line-by-one and return pandas's Series (this is a generator)
    # @param file Path to the input file to read
    def read(self, file=None, chunks_size=1, *args, **kwargs):
        # If the input file was not given in argument, we use the config
        if not file:
            file = self.config.config['datafile']

        # Check that variables values are possible
        if chunks_size < 1:
            chunks_size = 1

        # Read the Data file in chunks of 1000 lines (to avoid a too big memory footprint)
        datagen = pd.read_csv(file, iterator=True, chunksize=chunks_size, index_col=None, header=None, prefix='X')

        # Return one line (Series) of data from the generator
        for data in datagen:
            yield data

    ## Reset the cursor position to 0 (read the file back from the beginning)
    def resetpos(self, *args, **kwargs):
        BaseParser.resetpos(self, *args, **kwargs)

    ## Set the cursor position to read the file from a specified byte
    def setpos(self, pos=0, *args, **kwargs):
        BaseParser.setpos(self, pos, *args, **kwargs)
