#!/usr/bin/env python
# encoding: utf-8

## @package interframeparser
#
# Parse the data from a file containing interframes in CSV format

from oacs.inputparser.baseparser import BaseParser

from oacs.auxlib import *
import os
import itertools

import time
import StringIO

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
                                'FEATURE_METADATA': 4,                 # Feature containing meta data about other features
                                #'FEATURE_METAINTERFRAME': 5, # Meta data about the interframe (like the framerepeat, which should be used as a ponderation factor for all the others features)
                                #'FEATURE_LABEL': 6 # Not a feature, this is a label for the data
                                }

    # Which column(s) is/are the label(s) Y?
    featureTypeLabel = {'FEATURE_LABEL': 6}

    ## Constructor
    # @param config An instance of the ConfigParser class
    def __init__(self, config=None, *args, **kwargs):
        self.cursorpos = 0
        return BaseParser.__init__(self, config, *args, **kwargs)

    ## Load the whole content of a file containing interframes in CSV format and return pandas's DataFrames
    # @param file List of 2 elements, being the paths to the input types file and the input data file (in this order)
    # @param raw Return raw dataframe, without any column filtering
    def load(self, file=None, raw=False, *args, **kwargs):
        # If the input files were given in parameter, we update the config
        if file and (type(file) == list) and len(file) == 2:
            typesfile = file[0]
            datafile = file[1]
        else:
            typesfile = self.config.get('typesfile')
            datafile = self.config.get('datafile')

        # Get the list of columns we want to filter out (if specified), it is more efficient to do at parsing than later
        filtercols = self.config.get('parser_filter_columns')

        # Load the types from the types file
        self.types = pd.read_csv(typesfile, index_col=None, header=0) # squeeze=True does not work for row-oriented csv as of current pandas version!
        self.types = self.types.ix[0, :] # convert to a pandas Series

        # If we want raw data, we do not filter any column
        if raw:
            filtertypes = None
        # Else we filter out columns that are useless for learning
        else:
            filtertypes = self.types[~self.types.isin(self.featureTypeFilter.values())].keys() # get the list of columns we want to keep in the Data

        # Drop out the columns specified by the user in config
        if filtercols is not None:
            for col in filtercols:
                filtertypes = filtertypes.drop(col)

        # Read the Data file in chunks of 1000 lines (to avoid a too big memory footprint)
        data = pd.read_csv(datafile, iterator=True, chunksize=1000, usecols=filtertypes)
        X = pd.concat([chunk for chunk in data], ignore_index=True)

        # Extracting labels
        labels = self.types[self.types.isin(self.featureTypeLabel.values())].keys() # extracting all the column labels
        Y = X.ix[:,labels] # Extracting the columns into Y
        X = X.drop(labels, axis=1) # Drop the columns from X

        return {'X':X, 'Y':Y} # must always return a dict of variables

    ## Read interframes from a CSV file one-line-by-one and return pandas's Series (this is a generator)
    # Note: this implementation has no memory once it stops, so that you can't continue where you left last time (when you reached EOF)!
    # @param file List of 2 elements, being the paths to the input types file and the input data file (in this order)
    # @param raw Return raw dataframe, without any column filtering
    def __read_alt(self, file=None, raw=False, chunks_size=1, *args, **kwargs):
        # If the input files were given in parameter, we update the config
        if file and (type(file) == type(list)) and len(file) == 2:
            typesfile = file[0]
            datafile = file[1]
        else:
            typesfile = self.config.get('typesfile')
            datafile = self.config.get('datafile')

        # Check that variables values are possible
        if chunks_size < 1:
            chunks_size = 1

        self.types = pd.read_csv(typesfile, index_col=None, header=0) # squeeze=True does not work for row-oriented csv as of current pandas version!
        self.types = self.types.ix[0, :] # convert to a pandas Series

        # If we want raw data, we do not filter any column
        if raw:
            filtertypes = self.types[~self.types.isin(self.featureTypeLabel.values())].keys() # filter at least the Y label(s)
        # Else we filter out columns that are useless for learning
        else:
            filtertypes = self.types[~self.types.isin(self.featureTypeFilter.values() + self.featureTypeLabel.values())].keys() # get the list of columns we want to keep in the Data # z = dict(x); z.update(y);

        # Read the Data file in chunks of 1000 lines (to avoid a too big memory footprint)
        genX = pd.read_csv(datafile, iterator=True, chunksize=chunks_size, usecols=filtertypes)

        # Extracting labels
        labels = self.types[self.types.isin(self.featureTypeLabel.values())].keys() # extracting all the column labels
        genY = pd.read_csv(datafile, iterator=True, chunksize=chunks_size, usecols=labels)

        # Return the values of X and Y from the generators, and we fill the shortest list by None when we reach its end (but normally, we expect X and Y to have the same number of samples)
        for (X, Y) in itertools.izip_longest(genX, genY, fillvalue=None):
            yield {'X':X, 'Y':Y} # must always return a dict of variables

    def read(self, file=None, raw=False, skip_to_end=False, *args, **kwargs):
        # If the input files were given in parameter, we update the config
        if file and (type(file) == type(list)) and len(file) == 2:
            typesfile = file[0]
            datafile = file[1]
        else:
            typesfile = self.config.get('typesfile')
            datafile = self.config.get('datafile')

        # Skip to the end of the file (avoid redetecting the same samples)
        if skip_to_end and not self.getpos():
            self.setpos(pos='end', file=datafile)
            self.cursorpos = self.getpos()
        elif self.getpos() is None:
            self.setpos(0)

        # Read the types file to get metadata (columns names and columns types)
        self.types = pd.read_csv(typesfile, index_col=None, header=0) # squeeze=True does not work for row-oriented csv as of current pandas version!
        self.types = self.types.ix[0, :] # convert to a pandas Series

        # If we want raw data, we do not filter any column
        if raw:
            filtertypes = None
        # Else we filter out columns that are useless for learning
        else:
            filtertypes = self.types[~self.types.isin(self.featureTypeFilter.values())].keys() # get the list of columns we want to keep in the Data

        # Main loop to read the data from the file
        with open(datafile, 'rb') as f:

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
                X.index = self.types.index

                # Copy the raw sample
                X_raw = X

                # Filter out colums we don't want
                X = X[filtertypes]

                # Extracting labels
                labels = self.types[self.types.isin(self.featureTypeLabel.values())].keys() # extracting all the column labels
                Y = X[labels]
                X = X.drop(labels) # Drop the columns from X

                # Return a dict of generators
                yield {'X':X, 'Y':Y, 'X_raw':X_raw}

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
