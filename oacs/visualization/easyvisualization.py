#!/usr/bin/env python
# encoding: utf-8

## @package easyvisualization
#
# Compilation of functions to easily visualize the data. This is NOT to be used inside an autonomous OACS session (ie: from commandline), only at interactive shell or IPython Notebook.

import matplotlib.pylab as plt
import math

## A nice function to print 2 things side-by-side, by Wes McKinney
def side_by_side(*objs, **kwds):
    from pandas.core.common import adjoin
    space = kwds.get('space', 4)
    reprs = [repr(obj).split('\n') for obj in objs]
    print adjoin(space, *reprs)

## Get a set of random indexes inside the X dataset, in order to plot them
# @param X Samples Set
# @param maxn Maximum number of indexes to return (may return less if the number of indexes/rows in X is less than maxn)
def get_random_indexes(X, maxn):
    import random
    if X.shape[0] < maxn:
        rows_n = X.index
    else:
        rows_n = random.sample(X.index, maxn)
    return rows_n

## Get a set of random indexes inside the X dataset, in order to plot them
# Note: this function can account for the weights, it will give you more precise plots
# @param X Samples Set
# @param indexes Optionally, you can specify the indexes in X that you want to plot
# @param maxn Maximum number of indexes to plot (may return less if the number of indexes/rows in X is less than maxn)
def hist_all(X, indexes=None, maxn=100000, weights=None):
    import numpy as np
    if indexes is not None:
        rows_n = indexes
    else:
        rows_n = get_random_indexes(X, maxn)
    if weights is None and 'framerepeat' in X.columns:
        weights = X.ix[:,'framerepeat']
    #if weights is not None: # tile/repmat the weights
        #weights = weights.iloc[rows_n]
        #weights = np.tile(np.mat(weights), (len(X.columns), 1)).transpose()
    if weights is not None:
        weights = weights.ix[rows_n]
    for col in X.columns:
        plt.hist(X.ix[rows_n, col], bins=math.floor(len(rows_n)/100), normed=False, weights=weights)
        plt.title(str(col))
        plt.show()

## Reduce a dataset using PCA
# @param X Samples Set to reduce
# @param K Number of dimensions you will use in the reduction. How much loss for the K first eigenvectors?
# @param PCA_Threshold Maximum Variation Loss tolerated (between 0 and 1, 1 being 100%). At learning, can be used to find the best PCA_K. Default = 0.01 (= 1% tolerated)
def pca_reduce_all(X, K=None, Threshold=None, *args, **kwargs):
    from oacs.preoptimization.pca import PCA
    P = PCA
    dictofvars = P.optimize(X, PCA_K=K, PCA_Threshold=Threshold, *args, **kwargs)
    return dictofvars['X']

## Compute the PCA eigenvectors
# @return U,S,V
def pca_getvectors(X=None, Sigma2=None):
    from oacs.preoptimization.pca import PCA
    if Sigma2 is None and X is not None:
        from oacs.classifier.univariategaussian import UnivariateGaussian
        from oacs.classifier.multivariategaussian import MultivariateGaussian
        Mu = UnivariateGaussian.mean(X)
        Sigma2 = MultivariateGaussian.covar(X, Mu)
    if 'framerepeat' in Sigma2.columns:
        # drop the framerepeat key, we don't want to extract eigenvectors on this axis!
        Sigma2 = Sigma2.drop('framerepeat', axis=0).drop('framerepeat', axis=1)
    return PCA.compute_vectors(Sigma2)

def pca_findk(S, Threshold):
    from oacs.preoptimization.pca import PCA
    return PCA.find_best_dim(S, Threshold, True)

def pca_reduce(X, U, K):
    from oacs.preoptimization.pca import PCA
    return PCA.project(X, U, K)

def pca_loss(S, K):
    from oacs.preoptimization.pca import PCA
    return PCA.compute_variation_loss(S, K, True)

