#!/usr/bin/env python
# encoding: utf-8

## @package dropemptyfeatures
#
# Drop empty features (which always have the same value, and result in variance=0)

from oacs.preoptimization.basepreoptimization import BasePreOptimization

import pandas as pd

## DropEmptyFeatures
#
# Drop empty features (which always have the same value, and result in variance=0).
# These features are worthless because they do not convey any informations since they always hold the same value.
# In addition, they may crash the classifiers algorithms because of their degenerated property (0 variance, which will probably result in a division by zero).
class DropEmptyFeatures(BasePreOptimization):

    ## @var config
    # An instance of the ConfigParser object, already loaded

    ## Constructor
    # @param config An instance of the ConfigParser class
    def __init__(self, config=None, *args, **kwargs):
        return BasePreOptimization.__init__(self, config, *args, **kwargs)

    ## Drop empty features (which always have the same value, and result in variance=0)
    # @param X Samples set
    # @param Empty_features At detection, you can reload the previously learnt parameter here
    def optimize(self, X=None, Empty_features=None, *args, **kwargs):
        # Get the list of empty keys
        if Empty_features is not None:
            # At detection, reuse the previously learnt list of empty features
            emptykeys = Empty_features
        else:
            # At learning, compute to find the empty features
            # Variance = 0 <=> sure that this feature is empty
            emptykeys = X.columns[(~X.var().notnull()) | (X.var() == 0)].tolist() # equivalent to: X.columns[ (x == x.mean()).sum() == x.count() ] where we compare all values of a feature against its mean and see if at least one example has a different value

        # Remove the empty features
        # If at least one feature is empty, we remove it
        if len(emptykeys) > 0:
            if Empty_features is None: # print only at learning, not at detection
                print("Dropping empty feature(s) column(s): %s" % emptykeys) # Notify the user that we are dropping a few keys
            for key in emptykeys:
                if type(X) == pd.DataFrame:
                    if key in X.columns:
                            X = X.drop(key, axis=1) # Note: We could do it in one go with X = X.drop(emptykeys, axis=1) but it would fail if there were only a partial subset of the list of keys that are not yet removed and should be removed
                elif type(X) == pd.Series:
                    if key in X.keys():
                        X = X.drop(key)

        return {'X':  X, 'Empty_features': emptykeys } # always return a dict of variables if you want your variables saved durably and accessible later
