#!/usr/bin/env python
# encoding: utf-8

## @package detectionlog
#
# This contains the DetectionLog class to write down the positive detections in a log file

from oacs.postaction.basepostaction import BasePostAction
import numbers

## DetectionLog
#
# Write the positive detections in a log file
class DetectionLog(BasePostAction):

    ## @var config
    # A reference to a ConfigParser object, already loaded

    ## @var parent
    # A reference to the parent object (Runner)

    ## Constructor
    # @param config An instance of the ConfigParser class
    def __init__(self, config=None, parent=None, *args, **kwargs):
        self.defaultmsg = "$playerid was detected to be cheating at $timestamp with a probability of $Prediction"

        return BasePostAction.__init__(self, config, parent, *args, **kwargs)

    ## Write the positive detections in a log file
    # @param Cheater Is the player a cheater?
    # @param Playerinfo A dict containing the info of the last detected cheater
    # @param **kwargs(Any_Variable) Any other variable passed in argument will be substituted by its string representation
    def action(self, Cheater=False, Playerinfo=None, *args, **kwargs):
        # If player is not a cheater, we quit
        if not Cheater: return None

        detectionlog = self.config.get('detectionlog', 'detectionlog.txt')

        # Add the variables inside Playerinfo dict as variables themselves
        if Playerinfo is not None:
            kwargs.update(Playerinfo)

        # Load the template string to use for the lines
        template = self.config.get('detectionlogmsg', self.defaultmsg)

        # Substitute all variables in our template
        # For each available variable
        for key, value in kwargs.iteritems():
            # Try to replace the variable by its value if it's in the command
            try:
                # Check first that it's a printable object
                if isinstance(value, (int, long, float, complex, basestring, numbers.Number)):
                    try: # try to convert to int if possible, but if it crashes, we just pass (eg: strings will make this crash)
                        if (int(value) == value): value = int(value) # first try to convert the value to an int if it makes no difference (no info lost)
                    except Exception, e:
                        pass
                    template = template.replace("$%s" % key, str(value)) # replace all occurences of the variable key/name by its value (string representation of the value)
            # Error, we just pass
            except Exception, e:
                #print(e)
                pass

        with open(detectionlog, 'ab') as f:
            f.write("%s\n" % template)

        return True
