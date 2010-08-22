#! /usr/bin/env jython
# start.py

# This is a quick-and-dirty script to simplify running Grinder
# agent and console from the command-line.

usage = """Usage:

  jython start.py [agent|console]

This script reads configuration from conf.py in the current directory.
Please edit conf.py to fit your environment before running start.py.
"""

import os
import sys

# Get configuration from conf.py
from conf import paths

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print(usage)
        sys.exit()

    arg = sys.argv[1]
    if arg not in ('agent', 'console'):
        print(usage)
        sys.exit()

    abs = os.path.abspath

    # Add java home directory to system path
    new_path = abs(paths['java']) + os.path.pathsep + os.getenv('PATH')
    os.putenv('PATH', new_path)

    # Add grinder.jar to Java's classpath
    grinder_jar = abs(os.path.join(paths['grinder'], 'lib', 'grinder.jar'))
    classpath = grinder_jar + os.path.pathsep + os.getenv('CLASSPATH', '')

    # Assemble the command-line
    cmd = 'java -cp ' + classpath
    # Add Jython path
    cmd += ' -Dgrinder.jvm.arguments=-Dpython.home=' + abs(paths['jython'])

    # Add library name for agent or console
    # (Agent needs grinder.properties, but console does not)
    if arg == 'agent':
        cmd += ' net.grinder.Grinder ' + abs(paths['properties'])
    else:
        cmd += ' net.grinder.Console'

    print("Running: %s" % cmd)

    try:
        os.system(cmd)
    except KeyboardInterrupt:
        print("Stopped Grinder %s" % arg)


