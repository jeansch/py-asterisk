$Id$


Asterisk Manager API interface module for Python.

This module provides an object oriented interface to the Asterisk Manager API,
whilest embracing some applicable Python concepts:

    - Functionality is split into seperate mix-in classes.

    - Asterisk PBX errors cause fairly granular exceptions.

    - Docstrings are provided for all objects.

    - Asterisk data is translated into data stored using Python types, so
      working with it should be trivial. Through the use of XMLRPCServer or
      similar, it should be trivial to expose this conversion to other
      languages.

Using the Manager or CoreManager objects, or using your own object with the
CoreActions mix-in, you may simply call methods of the instanciated object and
they will block until all data is available.

Support for asynchronous usage is incomplete; consider running the client from
a thread and driven through a queue when integrating with an asynchronous
design.
