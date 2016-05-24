#!/usr/bin/env python

'''
Asterisk/CLI.py: Command-line wrapper around the Asterisk Manager API.
'''

# pylint: disable=W0710

from __future__ import absolute_import
from __future__ import print_function

import inspect
import os
import sys

from Asterisk import BaseException  # pylint: disable=W0622
from Asterisk import Config
from Asterisk import Manager
import Asterisk.Util

__author__ = 'David M. Wilson <dw@autosols.com>'
__id__ = '$Id$'


class ArgumentsError(BaseException):
    _prefix = 'bad arguments'


def usage(argv0, out_file):
    '''
    Print command-line program usage.
    '''
    argv0 = os.path.basename(argv0)
    usage_text = '''
        %(argv0)s actions
            Show available actions and their arguments.

        %(argv0)s action <API action> [<arg1> [<argn> ..]]
            Execute the specified action.
            For named arguments "--name=<val>" syntax may also be used.

        %(argv0)s command "<console command>"
            Execute the specified Asterisk console command.

        %(argv0)s usage
            Display this message.

        %(argv0)s help <action>
            Display usage message for the given <action>.

    ''' % locals()
    out_file.writelines([line[6:] + '\n' for line in usage_text.splitlines()])


def show_actions(action=None):
    if action is None:
        print()
        print('Supported actions and their arguments.')
        print('======================================')
        print()

    class AllActions(Manager.CoreActions, Manager.ZapataActions):
        pass

    methods = [(name, obj) for (name, obj) in inspect.getmembers(AllActions)
               if inspect.ismethod(obj) and name[0] != '_']

    if action is not None:
        methods = [x for x in methods if x[0].lower() == action.lower()]

    for name, method in methods:
        arg_spec = inspect.getargspec(method)
        arg_spec[0].pop(0)
        print('   Action:', name)
        fmt = inspect.formatargspec(*arg_spec)[1:-1]
        if fmt:
            print('Arguments:', fmt)
        lines = [x.strip() for x in method.__doc__.strip().splitlines()]
        print('           ' + '\n           '.join(lines))
        print()


def execute_action(manager, argv):
    method_name = argv.pop(0).lower()
    method_dict = dict((k.lower(), v) for (k, v) in inspect.getmembers(manager)
                       if inspect.ismethod(v))

    try:
        method = method_dict[method_name]
    except KeyError:
        raise ArgumentsError('%r is not a valid action.' % (method_name,))

    pos_args = []
    kw_args = {}
    process_kw = True

    for arg in argv:
        if process_kw and arg == '--':
            process_kw = False  # stop -- processing.
        elif process_kw and arg[:2] == '--' and '=' in arg:
            key, val = arg[2:].split('=', 2)
            kw_args[key] = val
        else:
            pos_args.append(arg)

    Asterisk.Util.dump_human(method(*pos_args, **kw_args))


def command_line(argv):
    '''
    Act as a command-line tool.
    '''
    commands = ('actions', 'action', 'command', 'usage', 'help')

    if len(argv) < 2:
        raise ArgumentsError('please specify at least one argument.')

    command = argv[1]

    if command not in commands:
        raise ArgumentsError('invalid arguments.')

    if command == 'usage':
        return usage(argv[0], sys.stdout)

    manager = Manager.Manager(*Config.Config().get_connection())

    if command == 'actions':
        show_actions()

    if command == 'help':
        if len(argv) < 3:
            raise ArgumentsError('please specify an action.')

        show_actions(argv[2])

    elif command == 'action':
        if len(argv) < 3:
            raise ArgumentsError('please specify an action.')

        try:
            execute_action(manager, argv[2:])
        except TypeError:
            print("Bad arguments specified. Help for %s:" % (argv[2],))
            show_actions(argv[2])

    elif command == 'command':
        execute_action('command', argv[2])
