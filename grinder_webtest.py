# grinder_webtest.py

"""A Grinder script that runs requests found in a .webtest XML file,
particularly those exported by Fiddler2.

To use this script, set the following in your grinder.properties:

    grinder.script = grinder_webtest.py
    grinder.think = <delay between requests, in milliseconds>

Then use webtest_sets to define which .webtest files to execute.
"""

# Everything in this script should be compatible with Jython 2.2.1.

from net.grinder.script.Grinder import grinder
from webtest.runner import TestSet, get_test_runner
from webtest.correlate import get_correlation_runner

# Get the name of .webtest file and think time from grinder.properties
webtest_think = grinder.properties.getInt('grinder.think', 500)

# Webtest sets
# This is a list of TestSets to be executed by TestRunner instances.  Each
# TestSet may include one or more .webtest filenames.  Any webtests that must
# be run sequentially in the same TestRunner instance should be included in the
# same TestSet; this allows variables captured in one of them to be carried
# over to the next webtest. If a webtest can be run independently of all
# others, then include it in a TestSet by itself.
before_set = TestSet()
after_set = TestSet()
test_sets = [
    TestSet(),
]


# Default values for variables
# Each of these will be stored separately by each TestRunner instance,
# but initializing them here allows every TestRunner to use these
# default values.
variables = {
}

# Get the base class for the TestRunner
TestRunner = get_test_runner(before_set, test_sets, after_set, 'thread', webtest_think, variables, 'info')
# Uncomment this to use a correlating TestRunner
#TestRunner = get_correlation_runner(before_set, test_sets, after_set, 'sequential', webtest_think, variables)


