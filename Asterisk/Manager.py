'''
Asterisk Manager API interface module for Python.

This module provides an object oriented interface to the Asterisk Manager API,
whilest embracing some applicable Python concepts:

    - Functionality is split into seperate mix-in classes.

    - Asterisk PBX errors cause fairly granular exceptions.

    - Docstrings are provided for all objects.

    - The module may be used asynchronously if required. It should be suitable
      for inclusion in a single-threaded GUI.

    - Asterisk data is translated into data stored using Python types, so
      working with it should be trivial. Through the use of XMLRPCServer or
      similar, it should be trivial to expose this conversion to other
      languages.


Synchronous Usage:

    Using the Manager or CoreManager objects, or using your own object with the
    CoreActions mix-in, you may simply call methods of the instanciated object
    and they will block until all data is available.


Asynchronous Usage:

    Declare on_<event> methods for each event you wish to monitor. Using the
    select module, create an inner loop similar to this:

        class MyManager(Asterisk.Manager):
            def on_Link(self, event):
                some_module.do_something(event)

        manager = MyManager()
        objects_to_watch = [ manager, gui, etc ]

        while True:
            for obj in select.select(objects_to_watch, [], [])[1]:
                if obj is manager:
                    manager.read()
                else if obj is gui:
                    gui.handle_event()


    If you need to watch many events, or perhaps you would like to monitor
    everything that is happening, you can define a fall-back event handler.
    This event handler is used when a more specific one is not found (note use
    of CoreManager):

        class AllEventsManager(Asterisk.CoreManager):
            def on_Event(self, event):
                some_module.do_something(event)

        ...
'''

__author__ = 'David M. Wilson <dw-py-asterisk-Manager.py@botanicus.net>'
__id__ = '$Id$'

import socket, time
from new import instancemethod
import Asterisk, Asterisk.Util




# Your ParentBaseException class should provide a __str__ method that combined
# _prefix and _error as  ('%s: %s' % (_prefix, _error) or similar.

class BaseException(Asterisk.BaseException):
    'Base class for all Asterisk Manager API exceptions.'
    _prefix = 'Asterisk'


class AuthenticationFailure(BaseException):
    'This exception is raised when authentication to the PBX instance fails.'
    _error = 'Authentication failed.'


class CommunicationError(BaseException):
    'This exception is raised when the PBX responds in an unexpected manner.'
    def __init__(self, packet, msg = None):
        e = 'Unexpected response %r from PBX' % (packet['Response'],)
        if msg: e += ' (' + msg + ')'
        self._error = e + ': %r' % (packet['Message'],)


class GoneAwayError(BaseException):
    'This exception is raised when the Manager connection becomes closed.'


class InternalError(BaseException):
    'This exception is raised when an error occurs within a Manager object.'
    _prefix = 'py-Asterisk internal error'


class ActionFailed(BaseException):
    'This exception is raised when a PBX action fails.'
    _prefix = 'py-Asterisk action failed'


class PermissionDenied(BaseException):
    '''
    This exception is raised when our connection is not permitted to perform a
    requested action.
    '''

    _error = 'Permission denied'




class BaseManager(object):
    'Base protocol implementation for the Asterisk Manager API.'

    _AST_BANNER = 'Asterisk Call Manager/1.0\r\n'


    def __init__(self, hostname, port, username, secret, listen_events = True):
        '''
        Provide communication methods for the PBX instance running at <hostname> on
        <port>. Authenticate using <username> and <secret>. Receive event
        information from the Manager API if <listen_events> is True.
        '''

        self.hostname = hostname
        self.port = port
        self.username = username
        self.secret = secret
        self.listen_events = listen_events

        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((hostname, port))

        self.file = sock.makefile('r+', 1) # line buffered.
        self.fileno = self.file.fileno
        self.response_buffer = []

        self._authenticate()


    def _authenticate(self):
        'Read the server banner and attempt to authenticate.'

        if self.file.readline() != self._AST_BANNER:
            raise Exception('Server banner was incorrect.')

        action = {
            'Username': self.username,
            'Secret': self.secret
        }

        if not self.listen_events:
            action['Events'] = 'off'

        self._write_action('Login', action)

        if self._read_packet()['Response'] == 'Error':
            raise AuthenticationFailure


    def __repr__(self):
        'Return a string representation of this object.'

        return '<%s.%s connected as %s to %s:%d>' %\
            (self.__module__, self.__class__.__name__,
             self.username, self.hostname, self.port)


    def _write_action(self, action, data = None):
        '''
        Write an <action> request to the Manager API, sending header keys and
        values from the mapping <data>. Return the (string) action identifier
        on success.
        '''

        id = str(time.time()) # Assumes microsecond precision for reliability.
        lines = [ 'Action: ' + action, 'ActionID: ' + id ]

        if data is not None:
            [ lines.append('%s: %s' % item) for item in data.iteritems() ]

        self.file.write('\r\n'.join(lines) + '\r\n\r\n')
        return id


    def _read_response_follows(self):
        '''
        Continue reading the remainder of this packet, in the format sent by
        the "command" action.
        '''

        lines = []
        packet = { 'Response': 'Follows', 'Lines': lines }

        while True:
            line = self.file.readline().rstrip()

            if not line or line == '--END COMMAND--':
                return packet

            lines.append(line)


    def _read_packet(self):
        '''
        Read a set of packet from the Manager API, stopping when a "\r\n\r\n"
        sequence is read. Return the packet as a mapping.
        '''

        packet = Asterisk.Util.AttributeDict()

        while True:
            line = self.file.readline().rstrip()

            if not line:
                if not packet:
                    raise GoneAwayError('Asterisk Manager connection has gone away.')

                return packet

            if line.count(':') == 1 and line[-1] == ':': # Empty field:
                key, val = line[:-1], ''
            else:
                key, val = line.split(': ', 1)

            if key == 'Response' and val == 'Follows':
                return self._read_response_follows()

            packet[key] = val


    def _dispatch_packet(self, packet):
        'Feed a single packet to an event handler.'

        if 'Response' in packet:
            return self.on_Response(packet)

        if 'Event' in packet:
            # Specific handler:
            method = getattr(self, 'on_%s' % packet['Event'], None)
            if method is not None:
                return method(packet)

            # Global handler:
            method = getattr(self, 'on_Event', None)
            if method is not None:
                return method(packet)

            raise InternalError(
                'no handler defined for event %(Event)r.' % packet)

        raise InternalError('Unknown packet type detected: %r'
            % (packet, ))


    def _raise_failure(self, packet, success = None):
        'Raise an error if the reponse packet reports failure.'

        if packet['Response'] in ('Success', 'follows'):
            return packet

        if packet['Message'] == 'Permission denied':
            raise PermissionDenied

        raise ActionFailed(packet['Message'])


    def close(self):
        'Log off and close the connection to the PBX.'

        self._write_action('Logoff')
        packet = self._read_packet()
        if packet['Response'] != 'Goodbye':
            raise CommunicationError(packet, 'expected goodbye')
        self.file.close()


    def read(self):
        'Called by the parent code when activity is detected on our fd.'

        packet = self._read_packet()
        self._dispatch_packet(packet)


    def read_response(self, id):
        'Return the response packet found for the given action <id>.'

        buffer = self.response_buffer

        while True:
            if buffer:
                for idx, packet in enumerate(buffer):
                    # It is an error if no ActionID is sent. This is intentional.
                    if packet['ActionID'] == id:
                        buffer.pop(idx)
                        return packet

            packet = self._read_packet()


            if 'Event' in packet:
                self._dispatch_packet(packet)

            elif not packet.has_key('ActionID'):
                raise CommunicationError(packet, 'no ActionID')

            elif packet['ActionID'] == id:
                return packet

            else:
                buffer.append(packet)


    def responses_waiting(self):
        'Return truth if there are unprocessed buffered responses.'

        return bool(self.response_buffer)


    def serve_forever(self):
        'Handle one event at a time until doomsday.'

        while True:
            packet = self._read_packet()
            self._dispatch_packet(packet)




class CoreEventHandlers(object):
    '''
    Provide placeholders for events generated by the core Asterisk engine.
    '''

    # Placeholder event handlers. We define these so that previously unseen
    # events cause an Exception and thus addition here, so we help to document
    # the waste that is Asterisk. See (and update) doc/events.txt for example
    # events.

    def on_Response(self, event):
        'Fired when a response is sent in reply to an action.'

    def on_Newexten(self, event):
        'Fired when a "Newexten" event is seen.'

    def on_Hangup(self, event):
        'Fired when a "Hangup" event is seen.'

    def on_Newchannel(self, event):
        'Fired when a "Newchannel" event is seen.'

    def on_Newstate(self, event):
        'Fired when a "Newstate" event is seen.'

    def on_Link(self, event):
        'Fired when a "Link" event is seen.'

    def on_Unlink(self, event):
        'Fired when an "Unlink" event is seen.'

    def on_Reload(self, event):
        'Fired when a "Reload" event is seen.'

    def on_ExtensionStatus(self, event):
        'Fired when an "ExtensionStatus" event is seen.'

    def on_Rename(self, event):
        'Fired when a "Rename" event is seen.'

    def on_Newcalleridid(self, event):
        'Fired when a "Newcallerid" event is seen.'

    def on_Alarm(self, event):
        'Fired when an "Alarm" event is seen.'

    def on_AlarmClear(self, event):
        'Fired when an "AlarmClear" event is seen.'

    def on_Agentcallbacklogoff(self, event):
        'Fired when an "Agentcallbacklogoff" event is seen.'

    def on_Agentcallbacklogin(self, event):
        'Fired when an "Agentcallbacklogin" event is seen.'

    def on_Agentlogin(self, event):
        'Fired when an "Agentlogin" event is seen.'

    def on_Agentlogoff(self, event):
        'Fired when an "Agentlogoff" event is seen.'

    def on_MeetmeJoin(self, event):
        'Fired when a "MeetmeJoin" event is seen.'

    def on_MeetmeLeave(self, event):
        'Fired when a "MeetmeLeave" event is seen.'

    def on_MessageWaiting(self, event):
        'Fired when a "MessageWaiting" event is seen.'

    def on_Join(self, event):
        'Fired when a "Join" event is seen.'

    def on_Leave(self, event):
        'Fired when a "Leave" event is seen.'

    def on_AgentCalled(self, event):
        'Fired when an "AgentCalled" event is seen.'

    def on_ParkedCall(self, event):
        'Fired when a "ParkedCall" event is seen.'

    def on_Cdr(self, event):
        'Fired when a "Cdr" event is seen.'

    def on_ParkedCallsComplete(self, event):
        'Fired when a "ParkedCallsComplete" event is seen.'

    def on_QueueParams(self, event):
        'Fired when a "QueueParams" event is seen.'

    def on_QueueMember(self, event):
        'Fired when a "QueueMember" event is seen.'

    def on_QueueStatusEnd(self, event):
        'Fired when a "QueueStatusEnd" event is seen.'

    def on_Status(self, event):
        'Fired when a "Status" event is seen.'

    def on_StatusComplete(self, event):
        'Fired when a "StatusComplete" event is seen.'




class CoreActions(object):
    '''
    Provide methods for Manager API actions exposed by the core Asterisk
    engine.
    '''

    def AbsoluteTimeout(self, channel, timeout):
        'Set the absolute timeout of <channel> to <timeout>.'

        id = self._write_action('AbsoluteTimeout', {
            'Channel': channel,
            'Timeout': int(timeout)
        })

        self._raise_failure(self.read_response(id))


    def ChangeMonitor(self, channel, pathname):
        'Change the monitor filename of <channel> to <pathname>.'

        id = self._write_action('ChangeMonitor', {
            'Channel': channel,
            'File': pathname
        })

        self._raise_failure(self.read_response(id))


    def Command(self, command):
        'Execute console command <command> and return its output lines.'

        id = self._write_action('Command', {'Command': command})
        return self._raise_failure(self.read_response(id))['Lines']


    def Events(self, categories):
        'Filter received events to only those in the list <categories>.'

        id = self._write_action('Events', { 'EventMask': ','.join(categories) })
        return self._raise_failure(self.read_response(id))


    def ExtensionState(self, context, extension):
        'Return the state of <extension> in <context>.'
        # TODO: what is this?

        id = self._write_action('ExtensionState', {
            'Context': context,
            'Exten': extension
        })
        return self._raise_failure(self.read_response(id))


    def Getvar(self, channel, variable, default = None):
        '''
        Return the value of <channel>'s <variable>, or <default> if <variable>
        is not set.
        '''

        id = self._write_action('Getvar', {
            'Channel': channel,
            'Variable': variable
        })

        response = self._raise_failure(self.read_response(id))
        value = response[variable]

        if value == '(null)':
            return default
        return value


    def Hangup(self, channel):
        'Hangup <channel>.'

        id = self._write_action('Hangup', { 'Channel': channel })
        return self._raise_failure(self.read_response(id))


    def ListCommands(self):
        'Return a dict of all available <action> => <desc> items.'

        id = self._write_action('ListCommands')
        commands = self._raise_failure(self.read_response(id))
        del commands['Response']
        return commands


    def Logoff(self):
        'Close the connection to the PBX.'

        return self.close()


    def MailboxCount(self, mailbox):
        'Return a (<new_msgs>, <old_msgs>) tuple for the given <mailbox>.'
        # TODO: this can sum multiple mailboxes too.

        id = self._write_action('MailboxCount', { 'Mailbox': mailbox })
        result = self._raise_failure(self.read_response(id))
        return int(result.NewMessages), int(result.OldMessages)


    def MailboxStatus(self, mailbox):
        'Return the number of messages in <mailbox>.'

        id = self._write_action('MailboxStatus', { 'Mailbox': mailbox })
        return int(self._raise_failure(self.read_response(id))['Waiting'])


    def Monitor(self, channel, pathname, format, mix):
        'Begin monitoring of <channel> into <pathname> using <format>.'

        id = self._write_action('Monitor', {
            'Channel': channel,
            'File': pathname,
            'Format': format,
            'Mix': mix and 'yes' or 'no'
        })

        return self._raise_failure(self.read_response(id))


    def Originate(self, channel, **kwargs):
        'Originate a call.'

        kwargs['Channel'] = channel
        id = self._write_action('Originate', kwargs)
        return self._raise_failure(self.read_response(id))


    def ParkedCalls(self):
        'Trigger resending of all parked call events.'

        id = self._write_action('ParkedCalls')
        return self._raise_failure(self.read_response(id))


    def Ping(self):
        'No-op to ensure the PBX is still there and keep the connection alive.'

        id = self._write_action('Ping')
        return self._raise_failure(self.read_response(id))


    def QueueAdd(self, queue, interface, penalty = 0):
        'Add <interface> to <queue> with optional <penalty>.'

        id = self._write_action('QueueAdd', {
            'Queue': queue,
            'Interface': interface,
            'Penalty': str(int(penalty))
        })

        return self._raise_failure(self.read_response(id))


    def QueueRemove(self, queue, interface):
        'Remove <interface> from <queue>.'

        id = self._write_action('QueueRemove', {
            'Queue': queue,
            'Interface': interface
        })

        return self._raise_failure(self.read_response(id))


    def Queues(self):
        'Return a complex nested dict describing queue statii.'

        id = self._write_action('QueueStatus')
        self._raise_failure(self.read_response(id))
        queues = {}

        def on_QueueParams(event):
            name = event.pop('Queue')
            event['members'] = {}
            del event['Event']

            queues[name] = event
    
        def on_QueueMember(event):
            del event['Event']
            queues[name]['member'][event.pop('Location')] = event

        def on_QueueStatusEnd(event):
            stop_flag[0] = True

        stop_flag = [ False ]

        old_QueueParams = self.on_QueueParams
        old_QueueMember = self.on_QueueMember
        old_QueueStatusEnd = self.on_QueueStatusEnd
        self.on_QueueParams = on_QueueParams
        self.on_QueueMember = on_QueueMember
        self.onQueueStatusEnd = on_QueueStatusEnd

        while stop_flag[0] == False:
            packet = self._read_packet()
            self._dispatch_packet(packet)

        self.on_QueueParams = old_QueueParams
        self.on_QueueMember = old_QueueMember
        self.onQueueStatusEnd = old_QueueStatusEnd

        return queues

    QueueStatus = Queues


    def Redirect(self, channel, context, extension, priority, channel2 = None):
        '''
        Redirect <channel> to <priority> of <extension> in <context>,
        optionally bridging with <channel2>
        '''

        id = self._write_action('Redirect', {
            'Channel': channel,
            'Context': context,
            'Exten': extension,
            'Priority': priority,
            'ExtraChannel': channel2 and channel2 or ''
        })

        return self._raise_failure(self.read_response(id))


    def SetCDRUserField(self, channel, data, append = False):
        "Append or replace <channel>'s CDR user field with <data>'."

        id = self._write_action('SetCDRUserField', {
            'Channel': channel,
            'UserField': data,
            'Append': append and 'yes' or 'no'
        })

        return self._raise_failure(self.read_response(id))


    def Setvar(self, channel, variable, value):
        'Set <variable> of <channel> to <value>.'

        id = self._write_action('Setvar', {
            'Channel': channel,
            'Variable': variable,
            'Value': value
        })

        return self._raise_failure(self.read_response(id))
 

    def Status(self):
        'Return a nested dict of channel statii.'

        id = self._write_action('Status')
        self._raise_failure(self.read_response(id))
        channels = {}

        def on_Status(self, event):
            name = event.pop('Channel')
            del event['Event']
            channels[name] = event
    
        def on_StatusComplete(self, event):
            stop_flag[0] = True

        stop_flag = [ False ]

        old_Status = self.on_Status
        old_StatusComplete = self.on_StatusComplete
        self.on_Status = instancemethod(on_Status, self, self.__class__)
        self.on_StatusComplete = instancemethod(on_StatusComplete, self, self.__class__)

        while stop_flag[0] == False:
            packet = self._read_packet()
            self._dispatch_packet(packet)

        self.on_Status = old_Status
        self.on_StatusComplete = old_StatusComplete

        return channels


    def StopMonitor(self, channel):
        'Stop monitoring of <channel>.'

        id = self._write_action('StopMonitor', { 'Channel': channel })
        return self._raise_failure(self.read_response(id))




class ZapataEventHandlers(object):
    '''
    Provide placeholders for events generated by the Zapata Driver.
    '''

    def on_ZapShowChannels(self, event):
        'Fired when a "ZapShowChannels" event is seen.'

    def on_ZapShowChannelsComplete(self, event):
        'Fired when a "ZapShowChannels" event is seen.'




class ZapataActions(object):
    'Provide methods for Manager API actions exposed by the Zapata driver.'

    def ZapDialOffhook(self, channel, number):
        'Off-hook dial <number> on Zapata driver <channel>.'

        id = self._write_action('ZapDialOffhook', {
            'ZapChannel': channel,
            'Number': number
        })

        return self._raise_failure(self.read_response(id))


    def ZapDNDoff(self, channel):
        'Disable DND status on Zapata driver <channel>.'

        id = self._write_action('ZapDNDoff', { 'ZapChannel': str(int(channel)) })
        return self._raise_failure(self.read_response(id))


    def ZapDNDon(self, channel):
        'Enable DND status on Zapata driver <channel>.'

        id = self._write_action('ZapDNDon', { 'ZapChannel': str(int(channel)) })
        return self._raise_failure(self.read_response(id))


    def ZapHangup(self, channel):
        'Hangup Zapata driver <channel>.'

        id = self._write_action('ZapHangup', { 'ZapChannel': str(int(channel)) })
        return self._raise_failure(self.read_response(id))


    def ZapShowChannels(self):
        'Return a nested dict of Zapata driver channel statii.'

        id = self._write_action('ZapShowChannels')
        self._raise_failure(self.read_response(id))
        channels = {}

        def on_ZapShowChannels(self, event):
            number = int(event.pop('Channel'))
            del event['Event']
            channels[number] = event
    
        def on_ZapShowChannelsComplete(self, event):
            stop_flag[0] = True

        stop_flag = [ False ]

        old_ZapShowChannels = self.on_ZapShowChannels
        old_ZapShowChannelsComplete = self.on_ZapShowChannelsComplete
        self.ZapShowChannels = on_ZapShowChannels
        self.on_ZapShowChannelsComplete = on_ZapShowChannelsComplete

        while stop_flag[0] == False:
            packet = self._read_packet()
            self._dispatch_packet(packet)

        self.on_ZapShowChannels = old_ZapShowChannels
        self.on_ZapShowChannelsComplete = old_ZapShowChannelsComplete

        return channels


    def ZapTransfer(self, channel):
        'Transfer Zapata driver <channel>.'
        # TODO: Does nothing on X100P. What is this for?

        id = self._write_action('ZapTransfer', { 'ZapChannel': str(int(channel)) })
        return self._raise_failure(self.read_response(id))




class CoreManager(BaseManager, CoreActions, ZapataActions):
    '''
    Asterisk Manager API protocol implementation and core actions, but without
    event handlers.
    '''

    pass




class Manager(BaseManager, CoreEventHandlers, CoreActions,
ZapataEventHandlers, ZapataActions):
    '''
    Asterisk Manager API protocol implementation, core event handler
    placeholders, and core actions.
    '''

    pass
