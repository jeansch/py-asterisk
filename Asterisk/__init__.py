'''
Asterisk Managemer API Python package.
'''

__author__ = 'David M. Wilson <dw@botanicus.net>'
__id__ = '$Id$'

try:
    __revision__ = int('$Rev$'.split()[1])
except:
    __revision__ = None

__version__ = '0.1'




class BaseException(Exception):
    '''
    Base class for all py-Asterisk exceptions.
    '''

    _prefix = '(Base Exception)'
    _error = '(no error)'

    def __init__(self, error):
        self._error = error

    def __str__(self):
        return '%s: %s' % (self._prefix, self._error)
