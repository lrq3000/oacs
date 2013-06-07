#!/usr/bin/env python
# encoding: utf-8

## @package weightedfeaturesnormalization
#
# Normalize the X dataset into a normal distribution (mean = 0, variance = 1) using weighted mean and variance

from oacs.preoptimization.basepreoptimization import BasePreOptimization
from oacs.classifier.univariategaussian import UnivariateGaussian
import pandas as pd

## FeaturesNormalization
#
# Normalize the X dataset into a normal distribution (mean = 0, variance = 1) using weighted mean and variance
class WeightedFeaturesNormalization(BasePreOptimization):

    ## @var config
    # An instance of the ConfigParser object, already loaded

    ## Constructor
    # @param config An instance of the ConfigParser class
    def __init__(self, config=None, *args, **kwargs):
        return BasePreOptimization.__init__(self, config, *args, **kwargs)

    ## Normalize the X dataset into a normal distribution (mean = 0, variance = 1)
    # @param X Samples set
    # @param Nonstd_Mu At detection, you can reload the previously learnt parameter here
    # @param Nonstd_Sigma2 At detection, you can reload the previously learnt parameter here
    def optimize(self, X=None, Y=None, Nonstd_Mu=None, Nonstd_Sigma2=None, *args, **kwargs):

        # Preparing the features: dropping examples labelled as anomalous, else it will fling out the stats
        if type(X) == pd.DataFrame:
            Yt = Y[Y==0].dropna() # get the list of non-anomalous examples
            Xt = X.iloc[Yt.index] # filter out anomalous examples and keep only non-anomalous ones
            # Note: we use other variable names because we only want to compute the stats on them (mean, variance), and then apply these on the WHOLE dataset, not just the one filtered here (anomalous examples included)
        else:
            Xt = X


        # Compute the weighted mean
        if Nonstd_Mu is None: # Only if it is not already computed
            Nonstd_Mu = UnivariateGaussian.mean(Xt)
        # Compute the variance
        if Nonstd_Sigma2 is None:
            Nonstd_Sigma2 = UnivariateGaussian.variance(Xt, Nonstd_Mu)
        # Avoiding NaNs
        Nonstd_Sigma2.fillna(1) # Simplification: if for a feature there's no variance at all (= 0), the feature will be NaN. This happens for example if there's no really any recorded data for the feature yet. We don't want that because it will break classifiers' predictions probabilities. Thus we set variance = 1 for these so that we say it's already a normally-spread distribution (thus below only the mean will normalize the feature, it's already centered)
        Nonstd_Sigma2[Nonstd_Sigma2 == 0.0] = 1 # Set 0 values to 1 (because else we will divide by zero, and get NaN!)
        # Backup the weights (because we don't want to lose them nor normalize them, we need them later for classification learning!)
        bak = None
        if 'framerepeat' in X.keys():
            bak = Xt['framerepeat']
        # Compute the normalized dataset
        # Note: we compute on X and NOT Xt because we want to return the WHOLE dataset, but normalized on the non-anomalous examples
        X_std = (X - Nonstd_Mu) * (1.0/Nonstd_Sigma2**0.5) # TODO: Bug Pandas or Numpy: never do X / var, but X * (1.0/var) or X * var**-1, else if you divide, python will continue to run in the background and use 25 percent CPU! https://github.com/pydata/pandas/issues/3407
        # Put back the weights
        if bak is not None: X_std['framerepeat'] = bak

        X_std = pd.DataFrame(X_std, columns = Xt.columns) # make sure the columns do not get scrambled up (this happens sometimes...) FIXME: remove this additional processing when pandas will be more stable...

        # Return the result
        # Either at learning we compute the mean and std, or either at detection we reload the learnt mean and std
        return {'X': X_std, 'Nonstd_Mu': Nonstd_Mu, 'Nonstd_Sigma2': Nonstd_Sigma2} # always return a dict of variables if you want your variables saved durably and accessible later
