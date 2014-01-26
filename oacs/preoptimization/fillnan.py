#!/usr/bin/env python
# encoding: utf-8

## @package fillnan
#
# Fill NaNs by copying other observed values (forward fill then backward fill)

from oacs.preoptimization.basepreoptimization import BasePreOptimization
from oacs.classifier.univariategaussian import UnivariateGaussian

## FillNaN
#
# Fill NaNs by copying other observed values (forward fill then backward fill)
# Necessary to take care of NaNs for mean, variance and covariance to compute correctly, and a lot of classifiers rely on these stats to work
class FillNaN(BasePreOptimization):

    ## @var config
    # An instance of the ConfigParser object, already loaded

    ## Constructor
    # @param config An instance of the ConfigParser class
    def __init__(self, config=None, *args, **kwargs):
        return BasePreOptimization.__init__(self, config, *args, **kwargs)

    ## Fill NaNs by copying other observed values (forward fill then backward fill)
    # @param X Samples set
    def optimize(self, X=None, *args, **kwargs):
        mode = self.config.get("fillnan_mode", "mean");
        if mode == "mean":
            Mean = UnivariateGaussian.mean(X);
            X = X.fillna(value=Mean, axis=0);
        else:
            # Forward fill first, which means we copy subsequent values of a feature to previous NaNs occurrences (because most of the NaNs will be because of the first frames when the engine could not set correctly all variables, so it's better to first begin to forward fill, this should be more reliable in our case)
            X = X.fillna(method='ffill', axis=0)
            # Backward fill remaining NaNs
            X = X.fillna(method='bfill', axis=0)
            # Check that we have filled all NaNs
            #if (sum(X.count() < X.shape[0])):
            #    print("FillNan warning: could not fill all NaNs, some NaNs are still in the dataset! Mean, variance and other classifier computations will probably fail!")

        # Return the NaNs-filled samples set
        return {'X':  X } # always return a dict of variables if you want your variables saved durably and accessible later
