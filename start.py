#! /usr/bin/env jython

# start.py
usage = """Usage: jython start.py [agent|console]"""

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

    if arg == 'agent':
        cmd = 'java -cp ' + classpath + \
              ' net.grinder.Grinder ' + abs(paths['properties'])

    else: # 'console'
        # Console does not need grinder.properties
        cmd = 'java -cp ' + classpath + ' net.grinder.Console'

    print("PATH: %s" % os.getenv('PATH'))
    print("CLASSPATH: %s" % classpath)
    print("Running: %s" % cmd)

