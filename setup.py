#!/usr/bin/env python

'''
py-Asterisk distutils script.
'''

from setuptools import setup

__author__ = 'David Wilson'
__id__ = '$Id$'


setup(name='py-Asterisk',
      version='0.5.10',
      description='Asterisk Manager API Python interface.',
      author='David Wilson',
      author_email='dw@botanicus.net',
      license='MIT',
      url='https://github.com/jeansch/py-asterisk/',
      packages=['Asterisk'],
      scripts=['asterisk-dump', 'py-asterisk'])
