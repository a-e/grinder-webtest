.. Grinder Webtest documentation master file, created by
   sphinx-quickstart on Tue Jun  8 17:32:38 2010.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Grinder Webtest
===============

You are reading the documentation for `Grinder Webtest`_, a custom module for
the Grinder_ load test framework designed to execute Visual Studio ``.webtest``
files.


Motivation
----------
This module was developed in order to work around some perceived limitations of
Grinder's built-in proxy-based HTTP recording. We found that in some cases,
Fiddler_ was able to more correctly and accurately record the HTTP requests
made by a web-enabled application. Since Fiddler is not designed for load
testing, it became necessary to find an alternative method for running the
scenarios it recorded.

Fiddler can export sessions in Visual Studio ``.webtest`` format, but Grinder
has no native support for this. Hence, this module was developed, to allow
transparent execution of these files as part of a load test. Since the
``.webtest`` format is plain-text XML, it's possible to extend it to allow
parameterization, response capturing and verification, with a minimum of
additional code.


Features
--------
* Run an arbitrary number of tests, with logical grouping in test sets
* Global and local variable parameters, with support for simple macros
* Capturing and verifying response output using regular expressions
* Sequential, thread-based, random, or weighted test sequencing
* Automatic numbering of individual tests for logging and reporting purposes
* Correlating test runner that matches parameters in HTTP responses
* Four configurable levels of logging verbosity


License
-------
This software is open source, under the terms of the `simplified BSD license`_.

.. _simplified BSD license: http://www.opensource.org/licenses/bsd-license.php


Installation
------------
You can obtain Grinder Webtest by downloading a official release from the
`downloads page`_, then extracting it to a location on your disk. In later
versions of Jython_, you can install like this::

    jython setup.py install

Alternatively, you can just build and run your tests directly in the source
directory (it'll probably work better that way).

If you want a copy of the latest development version, branch it from Launchpad_
using Bazaar_::

    bzr branch lp:grinder-webtest

The only dependency aside from Grinder is Jython_. Due to some limitations in
earlier versions of Grinder, this module was designed to work with Jython 2.2.1.

.. _downloads page: https://launchpad.net/grinder-webtest/+download


Setup
-----
In the root directory of the Grinder Webtest branch, you will find an example
``grinder_webtest.py`` script, along with a ``grinder.properties`` that uses
it. Refer to the Grinder_ documentation for more on how to use
``grinder.properties``, and how to run test scripts.

You can use ``grinder_webtest.py`` as the template for your test script; all
you need to do is include one or more `TestSet`\s containing ``.webtest``
files::

    test_sets = [
        TestSet('tests/test1.webtest'),
        TestSet('tests/test2.webtest'),
    ]

Then create a `TestRunner` class::

    TestRunner = get_test_runner(test_sets)

For the simplest tests, this is all you need to know. For more detail, refer
to the :doc:`runner` documentation.


Running
-------
To simplify the task of starting the Grinder console and/or agent, a
``start.py`` script is provided. This script reads configuration settings from
``conf.py``.

First, edit ``conf.py`` and define the appropriate pathnames for your
environment. On Linux, it might look something like this::

    paths = {
        'java':         '/usr/bin/java',
        'jython':       '/usr/local/share/jython',
        'grinder':      '/usr/share/grinder',
        'properties':   './grinder.properties',
    }

Save the changes to ``conf.py``. You can run the tests in a single agent
process like so::

    jython start.py agent

Or, if you would like to use the console, ensure your ``grinder.properties``
has ``grinder.useConsole=true``, then run the console::

    jython start.py console

Then start agents in separate terminals. Refer to the `Grinder docs`_ for more
information about the console, agents, and properties.


Modules
-------
.. toctree::
    :maxdepth: 1

    runner
    correlate
    parser


.. _Grinder Webtest: http://www.automation-excellence.com/software/grinder-webtest
.. _Grinder: http://grinder.sourceforge.net/
.. _Jython: http://www.jython.org/
.. _Fiddler: http://www.fiddler2.com/fiddler2/
.. _Launchpad: https://code.launchpad.net/grinder-webtest
.. _Bazaar: http://bazaar.canonical.com/
.. _Grinder docs: http://grinder.sourceforge.net/g3/getting-started.html

