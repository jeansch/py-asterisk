# 2015-01-04: New maintainer found (jeansch), thanks to David Wilson for all the past work !

# 2014-04-15: I have not used Asterisk in a decade. This package urgently needs a new maintainer!

# 2012-11-29: Downloads have been moved to Cheese Shop, to facilitate easier development

# http://pypi.python.org/pypi/py-Asterisk

--------


## Introduction

The Python Asterisk package (codenamed `py-Asterisk`) is an attempt
to produce high quality, well documented Python bindings for the Asterisk
Manager API.

The eventual goal of the package is to allow rich specification of the Asterisk
configuration in Python rather than in the quirky, unstructured, undocumented
mess that we call the Asterisk configuration files.


## Working Functionality

 * Python package implementing a manager client and event dispatcher.
 * User-oriented command line interface to manager API.


## Work In Progress

 * Introductory documentation for developers.
 * Asterisk module allowing dialplan configuration via the manager API (see [PbxConfigMgr my pbx_config_mgr page]).
 * Objects to represent the standard applications, for specification of dialplan configuration in a friendlier Python syntax.


## Documentation

Very little hand-written documentation is available yet for the package or it's
commands, however pydoc documentation for the `HEAD` revision can be found at
the link below. So far, only the beginnings of a developer's guide are
available. Although there is little content, it may help give you an overview
of programming with py-Asterisk.

    * [http://py-asterisk.googlecode.com/hg/doc/GUIDE.html?r=242456f432f2fa2727b26d648bcf7dc502fdcc51 Developer's guide documentation from intro_docs branch]


## Aims

* Provide a Python 2.3/2.4 package implementing an Asterisk Manager API client (*done*).
* Provide command-line tools to ease day-to-day Asterisk management and debugging (*done*).
* Provide objects for controlling and configuring Asterisk:
  * Provide a granular and intuitive event interface (*done*).
  * Provide all functionality encapsulated in flexible classes that may be mixed and reused easily (*done*).
  * Possibly provide rich data types for manipulation of Asterisk objects, for example '`some_channel.hangup()`' (*done*).

* Extend the manager API to encapsulate functionality only accessible through the Asterisk console and configuration files (<em>in progress</em>).
* Provide an IAX2 implementation, allowing for voice data to be generated from within Python (protocol bridge, IvR, experimentation, custom apps).
* Provide an enhanced and updated AGI module, and possible provide an EAGI module. 

If you have any ideas for this package, please contact me using the e-mail
address found on the main page of this site.
