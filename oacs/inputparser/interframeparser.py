#!/usr/bin/env python
# encoding: utf-8

## @package interframeparser
#
# Parse the data from a file containing interframes in CSV format

from oacs.inputparser.baseparser import BaseParser

from oacs.auxlib import *
import os
import itertools

import pandas as pd

## InterframeParser
#
# Parse the data from a file containing interframes in CSV format
class InterframeParser(BaseParser):
    ## @var config
    # An instance of the ConfigParser object, already loaded

    ## @var types
    # Contain the list of features names and their types (as int, because in the game interface we use an int enum)

    ## All the features we want to filter/hide from the learning process (except if we want the raw values)
    featureTypeFilter = {
                                'FEATURE_ID' : 0, 			# Identifier features
                                #'FEATURE_HUMAN': 1,			# Human-specific features
                                #'FEATURE_GAMESPECIFIC': 2,				# Game-specific features (game rules)
                                'FEATURE_PHYSICS': 3,                     # Physics limitation features (to avoid!!!)
                                #'FEATURE_METADATA': 4,                 # Feature containing meta data about other features (like the framerepeat, which should be used as a ponderation factor for all the others features)
                                #'FEATURE_LABEL': 5 # Not a feature, this is a label for the data
                                }

    # Which column(s) is/are the label(s) Y?
    featureTypeLabel = {'FEATURE_LABEL': 5}

    ## Constructor
    # @param config An instance of the ConfigParser class
    def __init__(self, config, *args, **kwargs):
        return BaseParser.__init__(self, config, *args, **kwargs)

    ## Load the whole content of a file containing interframes in CSV format and return pandas's DataFrames
    # @param file List of 2 elements, being the paths to the input types file and the input data file (in this order)
    # @param raw Return raw dataframe, without any column filtering
    def load(self, file=None, raw=False, *args, **kwargs):
        # If the input files were given in parameter, we update the config
        if file and (type(file) == type(list)) and len(file) == 2:
            self.config.config['typesfile'] = file[0]
            self.config.config['datafile'] = file[1]

        self.types = pd.read_csv(self.config.config['typesfile'], index_col=None, header=0) # squeeze=True does not work for row-oriented csv as of current pandas version!
        self.types = self.types.ix[0, :] # convert to a pandas Series

        # If we want raw data, we do not filter any column
        if raw:
            filtertypes = None
        # Else we filter out columns that are useless for learning
        else:
            filtertypes = self.types[~self.types.isin(self.featureTypeFilter.values())].keys() # get the list of columns we want to keep in the Data

        # Read the Data file in chunks of 1000 lines (to avoid a too big memory footprint)
        data = pd.read_csv(self.config.config['datafile'], iterator=True, chunksize=1000, usecols=filtertypes)
        X = pd.concat([chunk for chunk in data], ignore_index=True)

        # Extracting labels
        labels = self.types[self.types.isin(self.featureTypeLabel.values())].keys() # extracting all the column labels
        Y = X.ix[:,labels] # Extracting the columns into Y
        X = X.drop(labels, axis=1) # Drop the columns from X

        return {'X':X, 'Y':Y} # must always return a dict of variables

    ## Read interframes from a CSV file one-line-by-one and return pandas's Series (this is a generator)
    # @param file List of 2 elements, being the paths to the input types file and the input data file (in this order)
    # @param raw Return raw dataframe, without any column filtering
    def read(self, file=None, raw=False, chunks_size=1, *args, **kwargs):
        # If the input files were given in parameter, we update the config
        if file and (type(file) == type(list)) and len(file) == 2:
            self.config.config['typesfile'] = file[0]
            self.config.config['datafile'] = file[1]

        # Check that variables values are possible
        if chunks_size < 1:
            chunks_size = 1

        self.types = pd.read_csv(self.config.config['typesfile'], index_col=None, header=0) # squeeze=True does not work for row-oriented csv as of current pandas version!
        self.types = self.types.ix[0, :] # convert to a pandas Series

        # If we want raw data, we do not filter any column
        if raw:
            filtertypes = self.types[~self.types.isin(self.featureTypeLabel.values())].keys() # filter at least the Y label(s)
        # Else we filter out columns that are useless for learning
        else:
            filtertypes = self.types[~self.types.isin(self.featureTypeFilter.values() + self.featureTypeLabel.values())].keys() # get the list of columns we want to keep in the Data # z = dict(x); z.update(y);

        # Read the Data file in chunks of 1000 lines (to avoid a too big memory footprint)
        genX = pd.read_csv(self.config.config['datafile'], iterator=True, chunksize=chunks_size, usecols=filtertypes)

        # Extracting labels
        labels = self.types[self.types.isin(self.featureTypeLabel.values())].keys() # extracting all the column labels
        genY = pd.read_csv(self.config.config['datafile'], iterator=True, chunksize=chunks_size, usecols=labels)

        # Return the values of X and Y from the generators, and we fill the shortest list by None when we reach its end (but normally, we expect X and Y to have the same number of samples)
        for (X, Y) in itertools.izip_longest(genX, genY, fillvalue=None):
            yield {'X':X, 'Y':Y} # must always return a dict of variables

    def read_last(self, file=None, raw=False, chunks_size=1, *args, **kwargs):
        yield self.read(file=file, raw=raw, chunks_size=chunks_size, *args, **kwargs)

    ## Reset the cursor position to 0 (read the file back from the beginning)
    def resetpos(self, *args, **kwargs):
        BaseParser.resetpos(self, *args, **kwargs)

    ## Set the cursor position to read the file from a specified byte
    def setpos(self, pos=0, *args, **kwargs):
        BaseParser.setpos(self, pos, *args, **kwargs)
