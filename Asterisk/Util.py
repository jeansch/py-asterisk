'''
Asterisk/Util.py: utility classes.
'''

__author__ = 'David M. Wilson <dw-py-Asterisk-Util.py@botanicus.net>'
__Id__ = '$Id$'




class AttributeDict(dict):
    def __getattr__(self, key):
        return self[key]

    def __setattribute__(self, key, value):
        self[key] = value
