#!/usr/bin/env python

'''
py-Asterisk distutils script.
'''

__author__ = 'David Wilson'
__id__ = '$Id$'

from distutils.core import setup


setup(
    name =          'py-Asterisk',
    version =       '0.1',
    description =   'Asterisk Manager API Python interface.',
    author =        'David Wilson',
    license =       'MIT',
    url =           'http://py-asterisk.berlios.de/',
    packages =      [ 'Asterisk' ],
    scripts =       [ 'asterisk-dump', 'py-asterisk' ],
    data_files =    [ ('/etc/asterisk', ['conf/py-asterisk.conf.sample']) ]
)
