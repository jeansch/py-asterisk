'''
Asterisk/Util.py: utility classes.
'''

__author__ = 'David M. Wilson <dw-py-Asterisk-Util.py@botanicus.net>'
__Id__ = '$Id$'

import sys




class AttributeDict(dict):
    def __getattr__(self, key):
        return self[key]

    def __setattr__(self, key, value):
        self[key] = value




def dump_packet(packet, file = sys.stdout):
    '''
    Dump a packet in human readable form to file-like object <file>.
    '''

    packet = dict(packet)

    if 'Event' in packet:
        file.write('-- %s\n' % packet.pop('Event'))
    else:
        file.write('-- Response: %s\n' % packet.pop('Response'))


    packet = packet.items()
    packet.sort()

    for tuple in packet:
        file.write('   %s: %s\n' % tuple)

    file.write('\n')
