#!/usr/bin/env python
# encoding: utf-8

## @package dropemptyfeatures
#
# Drop empty features (which always have the same value, and result in variance=0)

from oacs.preoptimization.basepreoptimization import BasePreOptimization

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

    # Drop empty features (which always have the same value, and result in variance=0)
    # @param X Samples set
    def optimize(self, X=None, *args, **kwargs):
        # Variance = 0 <=> sure that this feature is empty
        emptykeys = X.columns[X.var() == 0] # equivalent to: X.columns[ (x == x.mean()).sum() == x.count() ] where we compare all values of a feature against its mean and see if at least one example has a different value
        # If at least one feature is empty, we remove it
        if len(emptykeys) > 0:
            X = X.drop(emptykeys, axis=1)
        # Return the NaNs-filled samples set
        return {'X':  X } # always return a dict of variables if you want your variables saved durably and accessible later
