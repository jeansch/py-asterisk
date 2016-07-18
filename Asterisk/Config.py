'''
Asterisk/Config.py: filesystem configuration reader.
'''

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
import os, sys

#configparser has changed
try:
    import configparser
except:
    import ConfigParser as configparser

import Asterisk

# Default configuration file search path:

CONFIG_FILENAME = 'py-asterisk.conf'

CONFIG_PATHNAMES = [
    os.environ.get('PYASTERISK_CONF', ''),
    os.path.join(os.environ.get('HOME', ''), '.py-asterisk.conf'),
    os.path.join(os.environ.get('USERPROFILE', ''), 'py-asterisk.conf'),
    'py-asterisk.conf',
    '/etc/py-asterisk.conf',
    '/etc/asterisk/py-asterisk.conf',
]


class ConfigurationError(Asterisk.BaseException):
    'This exception is raised when there is a problem with the configuration.'
    _prefix = 'configuration error'


# pylint: disable=W0710
class Config(object):
    def _find_config(self, config_pathname):
        '''
        Search the filesystem paths listed in CONFIG_PATHNAMES for a regular
        file.
        Return the name of the first one found, or <config_pathname>, if it
        is not None.
        '''

        if config_pathname is None:
            for pathname in CONFIG_PATHNAMES:
                if os.path.exists(pathname):
                    config_pathname = pathname
                    break

        if config_pathname is None:
            raise ConfigurationError(
                'Cannot find a suitable configuration file.')

        return config_pathname

    def refresh(self):
        'Read py-Asterisk configuration data from the filesystem.'

        try:
            self.conf = configparser.SafeConfigParser()
            self.conf.readfp(open(self.config_pathname))

        except configparser.Error as e:
            raise ConfigurationError('%r contains invalid data at line %r' %
                                     (self.config_pathname, e.lineno))

    def __init__(self, config_pathname=None):
        config_pathname = self._find_config(config_pathname)

        if config_pathname is None:
            raise ConfigurationError('Could not find a configuration file.')

        self.config_pathname = config_pathname
        self.refresh()

    def get_connection(self, connection=None):
        '''
        Return an (address, username, secret) argument tuple, suitable for
        initialising a Manager instance. If <connection> is specified, use
        the named <connection> instead of the configuration default.
        '''

        conf = self.conf

        try:
            if connection is None:
                connection = conf.get('py-asterisk', 'default connection')

            items = dict(conf.items('connection: ' + connection))

        except configparser.Error as e:
            raise ConfigurationError(str(e))

        try:
            address = (items['hostname'], int(items['port']))

        except ValueError:
            raise ConfigurationError('The port number specified is not valid.')

        return (address, items['username'], items['secret'])