$Id$


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
