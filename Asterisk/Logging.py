'''
Asterisk/Logging.py: extensions to the Python 2.3 logging module.
'''

from __future__ import absolute_import
import logging

__author__ = 'David Wilson'
__Id__ = '$Id$'


# Add new levels.

logging.STATE = logging.INFO - 1
logging.PACKET = logging.DEBUG - 1
logging.IO = logging.PACKET - 1

logging.addLevelName(logging.STATE, 'STATE')
logging.addLevelName(logging.PACKET, 'PACKET')
logging.addLevelName(logging.IO, 'IO')

# Attempt to find the parent logger class using the Python 2.4 API.

if hasattr(logging, 'getLoggerClass'):
    loggerClass = logging.getLoggerClass()
else:
    loggerClass = logging.Logger


# Provide a new logger class that supports our new levels.

class AsteriskLogger(loggerClass):
    def state(self, msg, *args, **kwargs):
        "Log a message with severity 'STATE' on this logger."
        return self.log(logging.STATE, msg, *args, **kwargs)

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

        return '%s.%s' % (self.__module__, self.__class__.__name__)

    def getLogger(self):
        '''
        Return the Logger instance which receives debug messages for this class
        instance.
        '''

        return logging.getLogger(self.getLoggerName())
