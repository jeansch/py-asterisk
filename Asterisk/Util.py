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




def _dump_result(result, file, _indent):
    indent = lambda a=0,i=_indent: ('   ' * (a+i))

    result.sort()

    for key, val in result:
        if isinstance(val, str):
            file.write('%s%s: %s\n' % (indent(), key, str(val)))
        elif isinstance(val, list):
            file.write('%s%s:\n%s' % (indent(), key, indent(1)))
            file.write(('\n' + indent(1)).join(map(str, val)))
            file.write('\n')
        elif isinstance(val, dict):
            file.write('%s%s:\n' % (indent(), key))
            _dump_result(val, file, _indent+1)


def dump_result(result, file = sys.stdout):
    '''
    Dump a nested dict in human readable form to file-like object <file>.
    '''

    if isinstance(result, dict):
        _dump_result(result.items(), file, 0)
    elif isinstance(result, (tuple, list)):
        _dump_result(list(enumerate(result)), file, 0)
