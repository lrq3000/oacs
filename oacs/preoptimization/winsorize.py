#!/usr/bin/env python
# encoding: utf-8

## @package winsorize
#
# Winsorizing the data to remove too extreme outliers values (equivalent of clipping in audio)

from oacs.preoptimization.basepreoptimization import BasePreOptimization

import pandas as pd
from scipy.stats import scoreatpercentile

## Winsorize
#
# Winsorizing the data to remove too extreme outliers values (equivalent of clipping in audio)
class Winsorize(BasePreOptimization):

    ## @var config
    # An instance of the ConfigParser object, already loaded

    ## Constructor
    # @param config An instance of the ConfigParser class
    def __init__(self, config=None, *args, **kwargs):
        return BasePreOptimization.__init__(self, config, *args, **kwargs)

    ## Winsorizing the data to remove too extreme outliers values (equivalent of clipping in audio)
    # @param X Samples set
    # @param Rate Winsorizing rate (between 0 and 100), which is the percentage of data you want to keep (eg: for 90%, extreme values above 95 percentile or below 5 percentile will be clipped)
    # TODO: account for weights in scoreatpercentile, here it does not account
    def optimize(self, X=None, Rate=90, *args, **kwargs):
        # Compute the complement of the rate
        r = (100-Rate)/2
        # Set the weights
        weights = ['framerepeat']

        # Get the extreme values
        extreme_low = pd.Series(scoreatpercentile(X, per=r, axis=0), index=X.columns)
        extreme_high = pd.Series(scoreatpercentile(X, per=100-r, axis=0), index=X.columns)

        # Winsorize (clip) the extreme values
        for feature in X.columns: # For each feature, we will clip all extreme values in one go
            # If this is the weights columns we skip
            if feature in weights: continue
            # Clip extremely low values
            X.ix[X.ix[:,feature] < extreme_low[feature], feature] = extreme_low[feature]
            # Clip extremely high values
            X.ix[X.ix[:,feature] > extreme_high[feature], feature] = extreme_high[feature]

        return {'X':  X } # always return a dict of variables if you want your variables saved durably and accessible later
