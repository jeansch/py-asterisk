'''
Asterisk/Util.py: utility classes.
'''
from __future__ import absolute_import


import sys

import Asterisk
from Asterisk import Logging

__author__ = 'David Wilson'
__Id__ = '$Id$'


class SubscriptionError(Asterisk.BaseException):
    '''
    This exception is raised when an attempt to register the same (event,
    handler) tuple twice is detected.
    '''

# This special unique object is used to indicate that an argument has not been
# specified. It is used where None may be a valid argument value.


class Unspecified(object):
    'A class to represent an unspecified value that cannot be None.'

    def __repr__(self):
        return '<Asterisk.Util.Unspecified>'

Unspecified = Unspecified()


class AttributeDict(dict):
    # Fields that can have more that one ocurrency in the manager response
    # or event
    MULTI_VALUE_FIELD = ('ChanVariable', 'DestChanVariable')

    def __setitem__(self, key, value):
        # Assign the multivalue fields correctly in the dictionary
        if key in self.MULTI_VALUE_FIELD and '=' in value:
            k, v = value.split('=')[:2]
            if key in self:
                self[key][k] = v
            else:
                super(AttributeDict, self).__setitem__(key, {k: v})
        else:
            super(AttributeDict, self).__setitem__(key, value)

    def __getattr__(self, key):
        return self[key]

    def __setattr__(self, key, value):
        self[key] = value

    def copy(self):
        return AttributeDict(iter(self.items()))


class EventCollection(Logging.InstanceLogger):
    '''
    Utility class to allow grouping and automatic registration of event.
    '''

    def __init__(self, initial=None):
        '''
        If <initial> is not None, register functions from the list <initial>
        waiting for events with the same name as the function.
        '''

        self.subscriptions = {}
        self.log = self.getLogger()

        if initial is not None:
            for func in initial:
                self.subscribe(func.__name__, func)

    def subscribe(self, name, handler):
        '''
        Subscribe callable <handler> to event named <name>.
        '''

        if name not in self.subscriptions:
            subscriptions = self.subscriptions[name] = []
        else:
            subscriptions = self.subscriptions[name]

        if handler in subscriptions:
            raise SubscriptionError("Duplicated subscription at event %r", (name))  # pylint: disable=W0710

        subscriptions.append(handler)

    def unsubscribe(self, name, handler):
        'Unsubscribe callable <handler> to event named <name>.'
        self.subscriptions[name].remove(handler)

    def clear(self):
        'Destroy all present subscriptions.'
        self.subscriptions.clear()

    def fire(self, name, *args, **kwargs):
        '''
        Fire event <name> passing *<args> and **<kwargs> to subscribers,
        returning the return value of the last called subscriber.
        '''

        if name not in self.subscriptions:
            return

        return_value = None

        for subscription in self.subscriptions[name]:
            self.log.debug('calling %r(*%r, **%r)', subscription, args, kwargs)
            return_value = subscription(*args, **kwargs)

        return return_value

    def copy(self):
        new = self.__class__()

        for name, subscriptions in self.subscriptions.items():
            new.subscriptions[name] = []
            for subscription in subscriptions:
                new.subscriptions[name].append(subscription)

    def __iadd__(self, collection):
        'Add all the events in <collection> to our collection.'

        if not isinstance(collection, EventCollection):
            raise TypeError

        new = self.copy()

        try:
            for name, handlers in collection.subscriptions.items():
                for handler in handlers:
                    self.subscribe(name, handler)
        except Exception:
            self.subscriptions = new.subscriptions
            raise

        return self

    def __isub__(self, collection):
        'Remove all the events in <collection> from our collection.'

        if not isinstance(collection, EventCollection):
            raise TypeError

        new = self.copy()

        try:
            for name, handlers in collection.subscriptions.items():
                for handler in handlers:
                    self.unsubscribe(name, handler)
        except Exception:
            self.subscriptions = new.subscriptions
            raise

        return self


def dump_packet(packet, file=sys.stdout):
    '''
    Dump a packet in human readable form to file-like object <file>.
    '''

    packet = dict(packet)

    if 'Event' in packet:
        file.write('-- %s\n' % packet.pop('Event'))
    else:
        file.write('-- Response: %s\n' % packet.pop('Response'))

    packet = list(packet.items())
    packet.sort()

    for tuple in packet:
        file.write('   %s: %s\n' % tuple)

    file.write('\n')


def dump_human(data, file=sys.stdout, _indent=0):

    recursive = (dict, list, tuple, AttributeDict)

    def indent(a=0, i=_indent):
        return '   ' * (a + i)

    Type = type(data)

    if Type in (dict, AttributeDict):
        items = list(data.items())
        items.sort()

        for key, val in items:
            file.write(indent() + str(key) + ': ')
            if any(isinstance(val, type_) for type_ in recursive):
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
