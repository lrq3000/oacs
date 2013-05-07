#!/usr/bin/env python
# encoding: utf-8

## @package playerinfo
#
# This class provides extended informations about a player in a variable Playerinfo

from oacs.postaction.basepostaction import BasePostAction

import datetime
import pandas as pd

## Playerinfo
#
# Provide extended informations about a player in a variable Playerinfo
class Playerinfo(BasePostAction):

    ## @var config
    # An instance of the ConfigParser object, already loaded

    ## Constructor
    # @param config An instance of the ConfigParser class
    def __init__(self, config=None, *args, **kwargs):
        return BasePostAction.__init__(self, config, *args, **kwargs)

    ## Provide extended informations about a player in a variable Playerinfo whenever a positive detection of a cheater occurs
    # @param X One sample (not the whole big set)
    # @param X_raw One raw sample: unfiltered columns (all the columns are available, even the one not used for detection nor learning like playerid)
    # @param Cheater Is the player a cheater?
    # @param Playerinfo A dict containing the info of the last detected cheater, if None this function will compute everything, else it will append more data fields
    def action(self, X=None, X_raw=None, Cheater=None, Playerinfo=None, *args, **kwargs):
        if Playerinfo is None: Playerinfo = dict()

        # Extract all fields of data available in the sample X
        if X is not None:
            Playerinfo.update(self._makePlayerinfoFromSample(Cheater=Cheater, X_raw=X))

        # If available, extract all fields of data available in the sample X_raw
        if X_raw is not None:
            Playerinfo.update(self._makePlayerinfoFromSample(Cheater=Cheater, X_raw=X_raw))

            # Compute human-readable datetime
            if 'timestamp' in X_raw.keys():
                Playerinfo['date'] = datetime.datetime.fromtimestamp(int(X_raw['timestamp'])).strftime('%Y-%m-%d')
                Playerinfo['time'] = datetime.datetime.fromtimestamp(int(X_raw['timestamp'])).strftime('%H:%M:%S')
                Playerinfo['datetime'] = datetime.datetime.fromtimestamp(int(X_raw['timestamp'])).strftime('%Y-%m-%d %H:%M:%S')

        return {'Playerinfo': Playerinfo}

    ## Make Playerinfo (extended player's infos, necessary for postactions) by extracting all the fields from the sample X
    def _makePlayerinfoFromSample(self, Cheater=None, X_raw=None, *args, **kwargs):
        # We can return a Playerinfo dict with extended informations identifying the player for futher processing by postaction classes
        Playerinfo = {'cheater': Cheater}
        # Check that it is one sample, a serie
        if X_raw is not None and type(X_raw) == pd.Series: Playerinfo.update(X_raw.to_dict()) # add all the informations available in Playerinfo
        return Playerinfo
