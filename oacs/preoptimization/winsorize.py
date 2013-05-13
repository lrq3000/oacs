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
    # @param winsorize_extreme_low At detection, you can reload the previously learnt parameter here
    # @param winsorize_extreme_high At detection, you can reload the previously learnt parameter here
    # TODO: account for weights in scoreatpercentile, here it does not account
    def optimize(self, X=None, Rate=98, winsorize_extreme_low=None, winsorize_extreme_high=None, *args, **kwargs):

        if self.config.config.get("winsorize_rate"):
            Rate = self.config.config.get("winsorize_rate")

        # Compute the complement of the rate
        r = (100-Rate)/2
        # Set the weights
        weights = ['framerepeat']

        # Get the extreme values
        if winsorize_extreme_low is not None and winsorize_extreme_high is not None:
            # Reload the parameters at detection
            extreme_low = winsorize_extreme_low
            extreme_high = winsorize_extreme_high
        else:
            # Compute the percentiles at learning
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

        # Technique for detection: at learning, we save the winsorization parameter to reload them at detection (else we would have no way to find the parameters from only one sample at detection)
        return {'X':  X, 'winsorize_extreme_low': extreme_low, 'winsorize_extreme_high': extreme_high } # always return a dict of variables if you want your variables saved durably and accessible later
