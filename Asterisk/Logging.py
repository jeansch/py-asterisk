'''
Asterisk/Logging.py: extensions to the Python 2.3 logging module.
'''

__author__ = 'David M. Wilson <dw-py-Asterisk-Util.py@botanicus.net>'
__Id__ = '$Id$'

import logging




# Add two new levels.

logging.PACKET = logging.DEBUG  - 1
logging.IO     = logging.PACKET - 1

logging.addLevelName(logging.PACKET, 'PACKET')
logging.addLevelName(logging.IO,     'IO')




# Attempt to find the parent logger class using the Python 2.4 API.

if hasattr(logging, 'getLoggerClass'):
    loggerClass = logging.getLoggerClass()
else:
    loggerClass = logging.Logger



# Provide a new logger class that supports our new levels.

class AsteriskLogger(loggerClass):
    def packet(self, msg, *args, **kwargs):
        "Log a message with severity 'PACKET' on this logger."
        return self.log(logging.PACKET, msg, *args, **kwargs)

    def io(self, msg, *args, **kwargs):
        "Log a message with severity 'IO' on this logger."
        return self.log(logging.IO, msg, *args, **kwargs)




# Install the new system-wide logger class.

logging.setLoggerClass(AsteriskLogger)



# Per-instance logging mix-in.

class InstanceLogger(object):
    def getLoggerName(self):
        '''
        Return the name where log messages for this instance is sent.
        '''

        return '%s.%s.%d' % (self.__module__, self.__class__.__name__, id(self))


    def getLogger(self):
        '''
        Return the Logger instance which receives debug messages for this class
        instance.
        '''

        return logging.getLogger(self.getLoggerName())
