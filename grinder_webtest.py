# grinder_webtest.py

"""A Grinder script that runs requests found in a .webtest XML file,
particularly those exported by Fiddler2.

To use this script, set the following in your grinder.properties:

    grinder.script = grinder_webtest.py

Then use test_sets to define which .webtest files to execute.
"""

# Everything in this script should be compatible with Jython 2.2.1.

# Uncomment this line if you need to use grinder methods, such as
# those that get values from grinder.properties
#from net.grinder.script.Grinder import grinder

# For example, if you wanted to get think time from grinder.properties
#webtest_think = grinder.properties.getInt('grinder.think', 500)


# Test Sets
# This is a list of TestSets to be executed by TestRunner instances.  Each
# TestSet may include one or more .webtest filenames.  Any webtests that must
# be run sequentially in the same TestRunner instance should be included in the
# same TestSet; this allows variables captured in one of them to be carried
# over to the next webtest. If a webtest can be run independently of all
# others, then include it in a TestSet by itself.
from webtest.runner import TestSet
test_sets = [
    #TestSet('first.webtest'),
    #TestSet('second.webtest'),
]


# Default values for variables
# Each of these will be stored separately by each TestRunner instance,
# but initializing them here allows every TestRunner to use these
# default values.
var_defaults = {
    #'USERNAME': 'Brian',
    #'PASSWORD': 'Nazareth',
}


# Define which test-runner-getter to use
from webtest.runner import get_test_runner
get_runner = get_test_runner

# Uncomment these two lines to use a correlating TestRunner instead
#from webtest.correlate import get_correlation_runner
#get_runner = get_correlation_runner


# Get the base class for the TestRunner
TestRunner = get_runner(
    test_sets,
    before_set=None,
    after_set=None,
    sequence='sequential',
    think_time=500,
    verbosity='info',
    variables=var_defaults)

