#!/usr/bin/env python

'''
Asterisk/CLI.py: Command-line wrapper around the Asterisk Manager API.
'''

__author__ = 'David M. Wilson <dw@autosols.com>'
__id__ = '$Id$'

import sys, inspect
from Asterisk import Manager, BaseException
from Asterisk.Config import get_config




class ArgumentsError(BaseException):
    _prefix = 'program arguments error'




def usage(argv0, out_file):
    '''
    Print command-line program usage.
    '''

    usage = '''
        %(argv0)s actions
            Show available actions and their arguments.
        %(argv0)s action <API action> [<arg1> [<argn> ..]]
            Execute the specified action.
        %(argv0)s command "<console command>"
            Execute the specified Asterisk console command.
        %(argv0)s usage
            Display this message.
    '''

    out_file.write(__doc__ + '\n')
    for line in usage.splitlines():
        out_file.write(line[8:]+'\n')
    out_file.write('\n')




def show_actions():
    print
    print "Supported actions and their arguments."
    print "======================================"
    print

    class AllActions(Manager.CoreActions, Manager.ZapataActions):
        pass

    methods = [
        (name, obj) for (name, obj) in inspect.getmembers(AllActions) \
        if inspect.ismethod(obj)
    ]

    for name, method in methods:
        arg_spec = inspect.getargspec(method)
        arg_spec[0].pop(0)
        print "   Action:", name

        fmt = inspect.formatargspec(*arg_spec)[1:-1]
        if fmt:
            print "Arguments:", fmt

        foo = [ x.strip() for x in method.__doc__.strip().splitlines() ]
        print '           ' + '\n           '.join(foo)
        print




def execute_action(manager, argv):
    method_name = argv.pop(0)
    method = getattr(manager, method_name)
    res = method(*argv)

    if isinstance(res, list):
        print '\n'.join(res)

    else:
        import pprint
        pprint.pprint(res)

    print


def command_line(argv):
    '''
    Act as a command-line tool.
    '''

    config = get_config()

    commands = [ 'actions', 'action', 'command', 'usage' ]

    if len(argv) < 2:
        raise ArgumentsError('please specify at least one argument.')

    command = argv[1]

    if command not in commands:
        raise ArgumentsError('invalid arguments.')



    if command == 'usage':
        return usage(argv[0], sys.stdout)

    manager = Manager.Manager(*get_config()['manager_init_args'])
    
    if command == 'actions':
        show_actions()

    elif command == 'action':
        if len(argv) < 3:
            raise ArgumentsError('please specify an action.')

        execute_action(manager, argv[2:])

    elif command == 'command':
        execute_action('command', argv[2])
