'''
Asterisk/Util.py: utility classes.
'''

__author__ = 'David M. Wilson <dw-py-Asterisk-Util.py@botanicus.net>'
__Id__ = '$Id$'

import sys, copy




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






def dump_human(data, file = sys.stdout, _indent = 0):
    scalars = (str, int, float)
    recursive = (dict, list, tuple, AttributeDict)
    indent = lambda a = 0, i = _indent: ('   ' * (a + i))
    Type = type(data)


    if Type in (dict, AttributeDict):
        items = data.items()
        items.sort()

        for key, val in items:
            file.write(indent() + str(key) + ': ')
            if type(val) in recursive:
                file.write('\n')
                dump_human(val, file, _indent + 1)
            else:
                dump_human(val, file, 0)

    elif Type in (list, tuple):
        for val in data:
            dump_human(val, file, _indent + 1)

    elif Type in (int, float):
        file.write(indent() + '%r\n' % data)

    elif Type is str:
        file.write(indent() + data + '\n')
