#! /usr/bin/env python
# setup.py

"""Installer for Grinder Webtest.
"""

from distutils.core import setup

setup(name='Grinder-Webtest',
      version='0.1',
      description='Wrapper for running .webtest files with Grinder',
      author='Eric Pierce',
      author_email='wapcaplet88@gmail.com',
      url='http://www.automation-excellence.com/software/grinder-webtest',
      license='Simplified BSD License',
      packages=['webtest'],
     )


