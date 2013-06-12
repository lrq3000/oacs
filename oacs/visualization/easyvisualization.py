#!/usr/bin/env python
# encoding: utf-8

## @package easyvisualization
#
# Compilation of functions to easily visualize the data. This is NOT to be used inside an autonomous OACS session (ie: from commandline), only at interactive shell or IPython Notebook.

import matplotlib.pylab as plt
import random
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
    if X.shape[0] < maxn:
        rows_n = X.index
    else:
        rows_n = random.sample(X.index, maxn)

## Get a set of random indexes inside the X dataset, in order to plot them
# @param X Samples Set
# @param indexes Optionally, you can specify the indexes in X that you want to plot
# @param maxn Maximum number of indexes to plot (may return less if the number of indexes/rows in X is less than maxn)
def hist_all(X, indexes=None, maxn=100000):
    if indexes is not None:
        rows_n = indexes
    else:
        get_random_indexes(X, maxn)
    for col in X.columns:
        plt.hist(X.ix[rows_n, col], bins=math.floor(len(rows_n)/100), normed=True)
        plt.title(str(col))
        plt.show()
