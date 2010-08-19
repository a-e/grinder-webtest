.. Grinder Webtest documentation master file, created by
   sphinx-quickstart on Tue Jun  8 17:32:38 2010.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Grinder Webtest documentation
=============================

You are reading the documentation for `Grinder Webtest`_, a custom module for
the Grinder_ load test framework designed to execute Visual Studio ``.webtest``
files.

Features
--------

* Run an arbitrary number of tests, with logical grouping in test sets
* Global and local variable parameters, with support for simple macros
* Capturing and verifying response output using regular expressions
* Sequential, thread-based, random, or weighted test sequencing

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


.. _Grinder Webtest: http://www.automation-excellence.com/software/grinder-webtest
.. _Grinder: http://grinder.sourceforge.net/
.. _Fiddler: http://www.fiddler2.com/fiddler2/

:mod:`runner`
=============
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
    :members:

:mod:`parser`
=============
.. automodule:: webtest.parser
    :members:


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

