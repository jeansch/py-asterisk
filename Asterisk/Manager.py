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

import socket, time, logging
from new import instancemethod
import Asterisk, Asterisk.Util



# Configure the logging module.

logging.PACKET = logging.DEBUG  - 1
logging.IO     = logging.PACKET - 1
logging.addLevelName(logging.PACKET, 'PACKET')
logging.addLevelName(logging.IO,     'IO')




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
        e = 'Unexpected response from PBX: %r\n' % (msg,)
        self._error = e + ': %r' % (packet,)


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




class BaseChannel(object):
    '''
    Represents a living Asterisk channel, with shortcut methods for operating
    on it. The object acts as a mapping, ie. you may get and set items of it.
    This translates to Getvar and Setvar actions on the channel.
    '''

    # Unique object used for testing for an unspecified argument where None is
    # unsuitable. We use this as it looks nice in pydoc output.
    _ChannelUnspecified = [None]

    def __init__(self, manager, channel_id):
        '''
        Initialise a new Channel object belonging to <channel_id> reachable via
        BaseManager <manager>.
        '''

        self.manager = manager
        self.channel_id = channel_id

    def __str__(self):
        return self.channel_id

    def __repr__(self):
        return '<%s.%s referencing channel %r of %r>' %\
            (self.__class__.__module__, self.__class__.__name__,
             self.channel_id, self.manager)

    def AbsoluteTimeout(self, timeout):
        'Set the absolute timeout of this channel to <timeout>.'
        return self.manager.AbsoluteTimeout(str(self), timeout)

    def ChangeMonitor(self, pathname):
        'Change the monitor filename of this channel to <pathname>.'
        return self.manager.ChangeMonitor(str(self), pathname)

    def Getvar(self, variable, default = _ChannelUnspecified):
        '''
        Return the value of this channel's <variable>, or <default> if variable
        is not set.
        '''
        if default is self._ChannelUnspecified:
            return self.manager.Getvar(str(self), variable)
        return self.manager.Getvar(str(self), variable, default)

    def Hangup(self):
        'Hangup this channel.'
        return self.manager.Hangup(str(self))

    def Monitor(self, pathname, format, mix):
        'Begin monitoring of this channel into <pathname> using <format>.'
        return self.manager.Monitor(str(self), pathname, format, mix)

    def Redirect(self, context, extension = 's', priority = 1, channel2 = None):
        '''
        Redirect this channel to <priority> of <extension> in <context>,
        optionally bridging with <channel2>.
        '''
        return self.manager.Redirect(str(self), context, extension, priority, channel2)

    def SetCDRUserField(data, append = False):
        "Append or replace this channel's CDR user field with <data>."
        return self.manager.SetCDRUserField(str(self), data, append)

    def Setvar(self, variable, value):
        'Set the <variable> in this channel to <value>.'
        return self.manager.Setvar(variable, value)

    def Status(self):
        'Return the Status() dict for this channel (wasteful!).'
        return self.manager.Status()[self.channel_id]

    def StopMonitor(self):
        'Stop monitoring of this channel.'
        return self.manager.StopMonitor(str(self))

    def __getitem__(self, key):
        'Fetch <key> as a variable from this channel.'
        return self.Getvar(key)

    def __setitem__(self, key, value):
        'Set <key> as a variable on this channel.'
        return self.Setvar(key, value)




class ZapChannel(BaseChannel):
    def ZapDNDoff(self):
        'Disable DND status on this Zapata driver channel.'
        return self.manager.ZapDNDoff(str(self))

    def ZapDNDon(self):
        'Enable DND status on this Zapata driver channel.'
        return self.manager.ZapDNDon(str(self))

    def ZapDialOffhook(self, number):
        'Off-hook dial <number> on this Zapata driver channel.'
        return self.manager.ZapDialOffhook(str(self), number)

    def ZapHangup(self):
        'Hangup this Zapata driver channel.'
        return self.manager.ZapHangup(str(self))

    def ZapTransfer(self):
        'Transfer this Zapata driver channel.'
        return self.manager.ZapTransfer(str(self))




class BaseManager(object):
    'Base protocol implementation for the Asterisk Manager API.'

    _AST_BANNER = 'Asterisk Call Manager/1.0\r\n'


    def getLoggerClass(self):
        '''
        Return the namespace where debug messages for all instances of this
        class are sent.
        '''

        return '%s.%s' % (self.__module__, self.__class__.__name__)


    def getLogger(self):
        '''
        Return the Logger instance which receives debug messages for this class
        instance.
        '''

        log_name = self.getLoggerClass() + '.' + str(id(self))
        return logging.getLogger(log_name)


    def __init__(self, address, username, secret, listen_events = True):
        '''
        Provide communication methods for the PBX instance running at
        <address>. Authenticate using <username> and <secret>. Receive event
        information from the Manager API if <listen_events> is True.
        '''

        self.address = address
        self.username = username
        self.secret = secret
        self.listen_events = listen_events


        self.log = self.getLogger()
        self.log.debug('Initialising.')


        # Configure logging:

        def _packetlog(msg, *args, **kwargs):
            self.log.log(logging.PACKET, msg, *args, **kwargs)

        def _iolog(msg, *args, **kwargs):
            self.log.log(logging.IO, msg, *args, **kwargs)

        self._iolog = _iolog
        self._packetlog = _packetlog


        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect(address)

        self.file = sock.makefile('r+', 1) # line buffered.
        self.fileno = self.file.fileno
        self.response_buffer = []

        self._authenticate()


    def _get_channel(self, channel_id):
        'Return a channel object for the given <channel_id>.'

        if channel_id[:3].lower() == 'zap':
            return ZapChannel(self, channel_id)
        return BaseChannel(self, channel_id)


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

        self.log.debug('Authenticating as %r/%r.', self.username, self.secret)
        self._write_action('Login', action)

        if self._read_packet().Response == 'Error':
            raise AuthenticationFailure

        self.log.debug('Authenticated as %r.', self.username)


    def __repr__(self):
        'Return a string representation of this object.'

        return '<%s.%s connected as %s to %s:%d>' %\
            ((self.__module__, self.__class__.__name__,
             self.username) + self.address)


    def _write_action(self, action, data = None):
        '''
        Write an <action> request to the Manager API, sending header keys and
        values from the mapping <data>. Return the (string) action identifier
        on success. Values from <data> are omitted if they are None.
        '''

        id = str(time.time()) # Assumes microsecond precision for reliability.
        lines = [ 'Action: ' + action, 'ActionID: ' + id ]

        if data is not None:
            [ lines.append('%s: %s' % item) for item in data.iteritems()
                if item[1] is not None ]

        self._packetlog('write_action: %r', lines)

        for line in lines:
            self.file.write(line + '\r\n')
            self._iolog('_write_action: send %r', line + '\r\n')

        self.file.write('\r\n')
        self._iolog('_write_action: send: %r', '\r\n')
        return id


    def _read_response_follows(self):
        '''
        Continue reading the remainder of this packet, in the format sent by
        the "command" action.
        '''

        self.log.debug('In _read_response_follows().')

        lines = []
        packet = Asterisk.Util.AttributeDict({
            'Response': 'Follows', 'Lines': lines
        })
        line_nr = 0

        while True:
            line = self.file.readline().rstrip()
            self._iolog('_read_response_follows: recv %r', line)
            line_nr += 1

            if line_nr == 1 and line.startswith('ActionID: '):
                # Asterisk is a pile of shite!!!!!!!!!
                packet.ActionID = line[10:]

            elif not line or line == '--END COMMAND--':
                self.file.readline()
                self.log.debug('Completed _read_response_follows().')
                return packet

            else:
                lines.append(line)


    def _read_packet(self, discard_events = False):
        '''
        Read a set of packet from the Manager API, stopping when a "\r\n\r\n"
        sequence is read. Return the packet as a mapping.
        
        If <discard_events> is True, discard all Event packets and wait for a
        Response packet, this is used while closing down the channel.
        '''

        packet = Asterisk.Util.AttributeDict()
        self.log.debug('In _read_packet().')

        while True:
            line = self.file.readline().rstrip()
            self._iolog('_read_packet: recv %r', line)

            if not line:
                if not packet:
                    raise GoneAwayError('Asterisk Manager connection has gone away.')

                self._packetlog('_read_packet: %r', packet)
                self.log.debug('_read_packet() completed.')
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
            self.log.debug('_dispatch_packet() placed response in buffer.')
            self.response_buffer.append(packet)

        elif 'Event' in packet:
            self._translate_event(packet)
            self.log.debug('_dispatch_packet() dealing with event.')

            # Specific handler:
            method = getattr(self, 'on_%s' % packet.Event, None)
            if method is not None:
                self.log.debug('_dispatch_packet() using on_%s', packet.Event)
                return method(packet)

            # Global handler:
            self.log.debug('_dispatch_packet() using on_Event for %r.', packet.Event)
            method = getattr(self, 'on_Event', None)
            if method is not None:
                return method(packet)

            raise InternalError('no handler defined for event %r.', packet.Event)

        else:
            raise InternalError('Unknown packet type detected: %r', packet)


    def _translate_response(self, packet, success = None):
        '''
        Raise an error if the reponse packet reports failure. Convert any
        channel identifiers to their equivalent objects using _get_channel().
        '''

        for key in ('Channel', 'Channel1', 'Channel2'):
            if key in packet:
                packet[key] = self._get_channel(packet[key])

        if packet.Response in ('Success', 'Follows', 'Pong'):
            return packet

        if packet.Message == 'Permission denied':
            raise PermissionDenied

        raise ActionFailed(packet.Message)


    def _translate_event(self, event):
        '''
        Translate any objects discovered in <event> to Python types.
        '''

        for key in ('Channel', 'Channel1', 'Channel2'):
            if key in event:
                event[key] = self._get_channel(event[key])


    def close(self):
        'Log off and close the connection to the PBX.'

        self.log.debug('close() shutting down.')

        self._write_action('Logoff')
        packet = self._read_packet(discard_events = True)
        if packet.Response != 'Goodbye':
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
                    if packet.ActionID == id:
                        buffer.pop(idx)
                        packet.pop('ActionID')
                        return packet

            packet = self._read_packet()


            if 'Event' in packet:
                self._dispatch_packet(packet)

            elif not packet.has_key('ActionID'):
                raise CommunicationError(packet, 'no ActionID')

            elif packet.ActionID == id:
                packet.pop('ActionID')
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


    def strip_evinfo(self, event):
        '''
        Given an event, remove it's ActionID and Event members.
        '''

        new = Asterisk.Util.AttributeDict(event)
        del new['ActionID'], new['Event']
        return new


    def replace_events(self, events):
        '''
        Given a list of functions, temporarily replace on_<funcname> attributes
        to self using those functions. Return a mapping containing undo
        information.
        '''

        output = {}
        for handler in events:
            handler_name = 'on_' + handler.__name__
            output[handler_name] = getattr(self, handler_name, None)
            setattr(self, handler_name,
                instancemethod(handler, self, self.__class__))

        return output


    def undo_events(self, mapping):
        '''
        Given a mapping (as returned by _save_methods), update self with those
        methods. Method names with a value of None are ignored.
        '''

        for name, method in mapping.iteritems():
            if method is None:
                del self.__dict__[name]
            else:
                setattr(self, name, method)




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

    def on_QueueEntry(self, event):
        'Fired when a "QueueEntry" event is seen.'

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

    # Unique object used for testing for an unspecified argument where None is
    # unsuitable. We use this as it looks nice in pydoc output.
    _CoreActionsUnspecified = [None]


    def AbsoluteTimeout(self, channel, timeout):
        'Set the absolute timeout of <channel> to <timeout>.'

        id = self._write_action('AbsoluteTimeout', {
            'Channel': channel,
            'Timeout': int(timeout)
        })

        self._translate_response(self.read_response(id))


    def ChangeMonitor(self, channel, pathname):
        'Change the monitor filename of <channel> to <pathname>.'

        id = self._write_action('ChangeMonitor', {
            'Channel': channel,
            'File': pathname
        })

        self._translate_response(self.read_response(id))


    def Command(self, command):
        'Execute console command <command> and return its output lines.'

        id = self._write_action('Command', {'Command': command})
        return self._translate_response(self.read_response(id))['Lines']


    def Events(self, categories):
        'Filter received events to only those in the list <categories>.'

        id = self._write_action('Events', { 'EventMask': ','.join(categories) })
        return self._translate_response(self.read_response(id))


    def ExtensionState(self, context, extension):
        'Return the state of <extension> in <context>.'
        # TODO: what is this?

        id = self._write_action('ExtensionState', {
            'Context': context,
            'Exten': extension
        })
        return self._translate_response(self.read_response(id))


    def Getvar(self, channel, variable, default = _CoreActionsUnspecified):
        '''
        Return the value of <channel>'s <variable>, or <default> if <variable>
        is not set.
        '''

        self.log.debug('Getvar(%r, %r, default=%r)', channel, variable, default)

        id = self._write_action('Getvar', {
            'Channel': channel,
            'Variable': variable
        })

        response = self._translate_response(self.read_response(id))
        value = response[variable]

        if value == '(null)':
            if default is self._CoreActionsUnspecified:
                raise KeyError(variable)
            else:
                self.log.debug('Getvar() returning %r', default)
                return default

        self.log.debug('Getvar() returning %r', value)
        return value


    def Hangup(self, channel):
        'Hangup <channel>.'

        id = self._write_action('Hangup', { 'Channel': channel })
        return self._translate_response(self.read_response(id))


    def ListCommands(self):
        'Return a dict of all available <action> => <desc> items.'

        id = self._write_action('ListCommands')
        commands = self._translate_response(self.read_response(id))
        del commands['Response']
        return commands


    def Logoff(self):
        'Close the connection to the PBX.'

        return self.close()


    def MailboxCount(self, mailbox):
        'Return a (<new_msgs>, <old_msgs>) tuple for the given <mailbox>.'
        # TODO: this can sum multiple mailboxes too.

        id = self._write_action('MailboxCount', { 'Mailbox': mailbox })
        result = self._translate_response(self.read_response(id))
        return int(result.NewMessages), int(result.OldMessages)


    def MailboxStatus(self, mailbox):
        'Return the number of messages in <mailbox>.'

        id = self._write_action('MailboxStatus', { 'Mailbox': mailbox })
        return int(self._translate_response(self.read_response(id))['Waiting'])


    def Monitor(self, channel, pathname, format, mix):
        'Begin monitoring of <channel> into <pathname> using <format>.'

        id = self._write_action('Monitor', {
            'Channel': channel,
            'File': pathname,
            'Format': format,
            'Mix': mix and 'yes' or 'no'
        })

        return self._translate_response(self.read_response(id))


    def Originate(self, channel, context = None, extension = None, priority = None,
    application = None, data = None, timeout = None, caller_id = None,
    variable = None, account = None, async = None):
        '''
        Originate(channel, context = .., extension = .., priority = ..[, ...])
        Originate(channel, application = ..[, data = ..[, ...]])

        Originate a call on <channel>, bridging it to the specified dialplan
        extension (format 1) or application (format 2).

            <context>       Dialplan context to bridge with.
            <extension>     Context extension to bridge with.
            <priority>      Context priority to bridge with.

            <application>   Application to bridge with.
            <data>          Application parameters.

            <timeout>       Answer timeout for <channel> in milliseconds.
            <caller_id>     Outgoing channel Caller ID.
            <variable>      channel variable to set (K=V[|K2=V2[|..]]).
            <account>       CDR account code.
            <async>         Return successfully immediately.
        '''

        has_dialplan = None not in (channel, context, extension)
        has_application = application is not None


        if has_dialplan and has_application:
            raise ActionFailed('Originate: dialplan and application calling style are mutually exclusive.')

        if not (has_dialplan or has_application):
            raise ActionFailed('Originate: neither dialplan or application calling style used. Refer to documentation.')

        if not channel:
            raise ActionFailed('Originate: you must specify a channel.')


        data = {
            'Channel': channel,             'Context': context,
            'Exten': extension,             'Priority': priority,
            'Application': application,     'Data': data,
            'Timeout': timeout,             'CallerID': caller_id,
            'Variable': variable,           'Account': account,
            'Async': int(bool(async))
        }

        id = self._write_action('Originate', data)
        return self._translate_response(self.read_response(id))


    def Originate2(self, channel, parameters):
        '''
        Originate a call, using parameters in the mapping <parameters>.
        Provided for compatibility with RPC bridges that do not support keyword
        arguments.
        '''

        return self.Originate(channel, **parameters)


    def ParkedCalls(self):
        'Return a nested dict describing currently parked calls.'

        id = self._write_action('ParkedCalls')
        self._translate_response(self.read_response(id))
        parked = {}

        def ParkedCall(self, event):
            event = self.strip_evinfo(event)
            parked[event.pop('Exten')] = event

        def ParkedCallsComplete(self, event):
            stop_flag[0] = True

        stop_flag = [ False ]
        undo = self.replace_events([ ParkedCall, ParkedCallsComplete ])

        try:
            while stop_flag[0] == False:
                packet = self._read_packet()
                self._dispatch_packet(packet)

        finally:
            self.undo_events(undo)
        return parked




    def Ping(self):
        'No-op to ensure the PBX is still there and keep the connection alive.'

        id = self._write_action('Ping')
        return self._translate_response(self.read_response(id))


    def QueueAdd(self, queue, interface, penalty = 0):
        'Add <interface> to <queue> with optional <penalty>.'

        id = self._write_action('QueueAdd', {
            'Queue': queue,
            'Interface': interface,
            'Penalty': str(int(penalty))
        })

        return self._translate_response(self.read_response(id))


    def QueueRemove(self, queue, interface):
        'Remove <interface> from <queue>.'

        id = self._write_action('QueueRemove', {
            'Queue': queue,
            'Interface': interface
        })

        return self._translate_response(self.read_response(id))


    def QueueStatus(self):
        'Return a complex nested dict describing queue statii.'

        id = self._write_action('QueueStatus')
        self._translate_response(self.read_response(id))
        queues = {}

        def QueueParams(self, event):
            queue = self.strip_evinfo(event)
            queue['members'] = {}
            queue['entries'] = {}
            queues[queue.pop('Queue')] = queue
    
        def QueueMember(self, event):
            member = self.strip_evinfo(event)
            queues[member.pop('Queue')]['members'][member.pop('Location')] = member
            
        def QueueEntry(self, event):
            entry = self.strip_evinfo(event)
            queues[entry.pop('Queue')]['entries'][event.pop('Channel')] = entry

        def QueueStatusEnd(self, event):
            stop_flag[0] = True

        stop_flag = [ False ]

        undo = self.replace_events([ QueueParams, QueueMember, QueueEntry, QueueStatusEnd ])

        try:
            while stop_flag[0] == False:
                packet = self._read_packet()
                self._dispatch_packet(packet)

        finally:
            self.undo_events(undo)
        return queues

    Queues = QueueStatus


    def Redirect(self, channel, context, extension = 's', priority = 1, channel2 = None):
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

        return self._translate_response(self.read_response(id))


    def SetCDRUserField(self, channel, data, append = False):
        "Append or replace <channel>'s CDR user field with <data>'."

        id = self._write_action('SetCDRUserField', {
            'Channel': channel,
            'UserField': data,
            'Append': append and 'yes' or 'no'
        })

        return self._translate_response(self.read_response(id))


    def Setvar(self, channel, variable, value):
        'Set <variable> of <channel> to <value>.'

        id = self._write_action('Setvar', {
            'Channel': channel,
            'Variable': variable,
            'Value': value
        })

        return self._translate_response(self.read_response(id))
 

    def Status(self):
        'Return a nested dict of channel statii.'

        id = self._write_action('Status')
        self._translate_response(self.read_response(id))
        channels = {}

        def Status(self, event):
            event = self.strip_evinfo(event)
            name = event.pop('Channel')
            channels[name] = event
    
        def StatusComplete(self, event):
            stop_flag[0] = True


        stop_flag = [ False ]
        undo = self.replace_events([ Status, StatusComplete ])

        try:
            while stop_flag[0] == False:
                packet = self._read_packet()
                self._dispatch_packet(packet)

        finally:
            self.undo_events(undo)
        return channels


    def StopMonitor(self, channel):
        'Stop monitoring of <channel>.'

        id = self._write_action('StopMonitor', { 'Channel': channel })
        return self._translate_response(self.read_response(id))




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

        return self._translate_response(self.read_response(id))


    def ZapDNDoff(self, channel):
        'Disable DND status on Zapata driver <channel>.'

        id = self._write_action('ZapDNDoff', { 'ZapChannel': str(int(channel)) })
        return self._translate_response(self.read_response(id))


    def ZapDNDon(self, channel):
        'Enable DND status on Zapata driver <channel>.'

        id = self._write_action('ZapDNDon', { 'ZapChannel': str(int(channel)) })
        return self._translate_response(self.read_response(id))


    def ZapHangup(self, channel):
        'Hangup Zapata driver <channel>.'

        id = self._write_action('ZapHangup', { 'ZapChannel': str(int(channel)) })
        return self._translate_response(self.read_response(id))


    def ZapShowChannels(self):
        'Return a nested dict of Zapata driver channel statii.'

        id = self._write_action('ZapShowChannels')
        self._translate_response(self.read_response(id))
        channels = {}

        def ZapShowChannels(self, event):
            event = self.strip_evinfo(event)
            number = int(event.pop('Channel'))
            channels[number] = event
    
        def ZapShowChannelsComplete(self, event):
            stop_flag[0] = True

        stop_flag = [ False ]
        undo = self.replace_events([ ZapShowChannels, ZapShowChannelsComplete ])

        try:
            while stop_flag[0] == False:
                packet = self._read_packet()
                self._dispatch_packet(packet)

        finally:
            self.undo_events(undo)
        return channels


    def ZapTransfer(self, channel):
        'Transfer Zapata driver <channel>.'
        # TODO: Does nothing on X100P. What is this for?

        id = self._write_action('ZapTransfer', { 'ZapChannel': str(int(channel)) })
        return self._translate_response(self.read_response(id))




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
