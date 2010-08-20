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

Fiddler can export a session in Visual Studio ``.webtest`` format, but Grinder
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
* Correlating test runner that matches parameters in HTTP responses
* Four configurable levels of logging verbosity


Installation
------------
To install Grinder Webtest, obtain a copy of the branch from Launchpad_ using
Bazaar_::

    bzr branch lp:grinder-webtest

At present, there are no official release packages, and no installed
components; simply modify the files in your branch to suit your testing needs.


Usage
-----
In the root directory of the Grinder Webtest branch, you will find an example
``grinder_webtest.py`` script, along with a ``grinder.properties`` which uses
it. Refer to the Grinder_ documentation for more on how to use
``grinder.properties``, and how to run test scripts.

You can use ``grinder_webtest.py`` as the basis for your test script; all you
need to do is include one or more `TestSet`\s containing ``.webtest`` files::

    test_sets = [
        TestSet('tests/test1.webtest'),
        TestSet('tests/test2.webtest'),
    ]

For the simplest tests, this is all you need to know. For more detail, refer
to the `webtest.runner` module documentation.


:mod:`webtest.runner`
=====================

.. automodule:: webtest.runner

TestSet
-------
.. autoclass:: webtest.runner.TestSet
    :members:

get_test_runner
---------------
.. autofunction:: webtest.runner.get_test_runner

WebtestRunner
-------------
.. autoclass:: webtest.runner.WebtestRunner
    :members: set_class_attributes, eval_expressions, eval_capture

:mod:`webtest.correlate`
========================

.. automodule:: webtest.correlate
    :members:


:mod:`webtest.parser`
=====================

.. automodule:: webtest.parser
    :members:


Indices and tables
==================

* :ref:`genindex`
* :ref:`search`


.. _Grinder Webtest: http://www.automation-excellence.com/software/grinder-webtest
.. _Grinder: http://grinder.sourceforge.net/
.. _Fiddler: http://www.fiddler2.com/fiddler2/
.. _Launchpad: https://code.launchpad.net/grinder-webtest
.. _Bazaar: http://bazaar.canonical.com/

