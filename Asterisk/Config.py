'''
Asterisk/Config.py: filesystem configuration reader.
'''

import os, ConfigParser
import Asterisk


# Default configuration search path:

CONFIG_PATHNAMES = [
    os.environ.get('PYASTERISK_CONF', '/') + '/py-asterisk.conf',
    os.environ.get('HOME', '/') + '/.py-asterisk.conf',
    './py-asterisk.conf', '/etc/py-asterisk.conf',
    '/etc/asterisk/py-asterisk.conf',
]




class ConfigurationError(Asterisk.BaseException):
    'This exception is raised when there is a problem with the configuration.'
    _prefix = 'configuration error'




def get_config(config_pathname = None):
    '''
    Read py-Asterisk configuration data from the filesystem.
    '''

    if config_pathname is None:
        for pathname in CONFIG_PATHNAMES:
            if os.path.exists(pathname):
                config_pathname = pathname
                break

    if config_pathname is None:
        raise ConfigurationError('cannot find a suitable configuration file.')


    try:
        conf = ConfigParser.SafeConfigParser()
        conf.readfp(file(config_pathname))

    except ConfigParser.Error, e:
        raise ConfigurationError('%r contains invalid data at line %r' %\
            (config_pathname, e.lineno))


    return {
        'manager_init_args': (
            conf.get    ('pbx-connection', 'hostname'),
            conf.getint ('pbx-connection', 'port'),
            conf.get    ('pbx-connection', 'username'),
            conf.get    ('pbx-connection', 'secret'),
        )
    }
