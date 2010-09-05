# correlate.py

"""This module provides a subclass of `~webtest.runner.WebtestRunner` designed
to aid you with finding parameter values in HTTP responses. It does this by
attempting to match parameter names found in each request to the response body
of any HTTP request that preceded it.

To use it, simply call `get_correlation_runner` in the same way that you call
`~webtest.runner.get_test_runner`. When you run your main script, the log output
will include additional information about which responses contain certain
parameter names; this is useful in determining where you might be able to capture
parameter values.

Note that the correlating test runner is much slower and more memory-intensive
than the normal test runner (not to mention it can produce some gigantic log
files). Use this only during development of your scripts, and never for an
actual load test!
"""

# Import the necessary Grinder stuff
# This is wrapped with exception handling, to allow Sphinx to import this
# module for documentation purposes
try:
    from net.grinder.script.Grinder import grinder
except ImportError:
    print("Grinder module import failed.")
    print("You may need to add grinder.jar to your classpath.")
    print("Continuing blissfully onward...")
else:
    log = grinder.logger.output

from runner import WebtestRunner

class CorrelationRunner (WebtestRunner):
    """A WebtestRunner that correlates requests and responses.
    """
    def __init__(self, **variables):
        # Dict of lists of HTTPResponses, indexed by webtest filename
        # (This must be initialized before WebtestRunner.__init__,
        # since __init__ may run before_set tests)
        self.webtest_responses = {}
        WebtestRunner.__init__(self, **variables)


    def run_test_set(self, test_set):
        """Overridden from WebtestRunner base class, to record the
        response for each request.
        """
        for filename in test_set.filenames:
            log("========== Executing: %s ==========" % filename)
            # Add an empty list to the responses dict, if it doesn't exist
            if filename not in self.webtest_responses:
                self.webtest_responses[filename] = []

            # Execute all requests in this test set, in order
            for test, wrapper, request in WebtestRunner.webtest_requests[filename]:
                # Try to correlate this request with previous responses
                # in the current webtest file
                self.correlate(filename, request)

                # Execute this request
                try:
                    response = self.execute(test, wrapper, request)
                # If problems occurred, report an error and re-raise
                except RuntimeError:
                    grinder.statistics.forLastTest.success = False
                    raise
                # Otherwise, store the test number and response body
                else:
                    body = response.getText()
                    self.webtest_responses[filename].append((test.getNumber(), body))

                # If response was not valid, report an error
                if response.getStatusCode() >= 400:
                    grinder.statistics.forLastTest.success = False

                # Sleep
                grinder.sleep(WebtestRunner.think_time)


    def correlate(self, filename, request):
        """Attempt to correlate parameters in the given request to
        any responses already received for the current webtest file.
        """
        # Get any existing responses, or an empty list
        responses = self.webtest_responses.get(filename, [])
        # If there are no responses yet for this filename, return
        if not responses:
            return

        log("====== Correlating request parameters")

        # For each parameter in the request, search backwards through
        # the existing responses and see if any of them contain the
        # parameter name.
        for name, value in request.parameters:
            # Don't look for parameters that already have a variable set
            if name in self.variables:
                log(":-) '%s' parameter already set or captured, skipping" % name)
                continue

            # Don't bother looking for parameters that have an empty value
            if value == '':
                log("... '%s' value is empty, skipping" % name)
                continue

            # Which test numbers have a response containing this parameter?
            found_in_tests = []

            # Examine each response and see whether it contains this parameter
            for test_number, body in responses:
                if name in body:
                    found_in_tests.append(str(test_number))

            # Log which test numbers this parameter was found in
            if found_in_tests:
                log("+++ '%s' found in response from test number(s): %s" % \
                    (name, ', '.join(found_in_tests)))
            else:
                log("--- '%s' not found in any response" % name)

        log("====== End of correlation")



def get_correlation_runner(test_sets,
                           before_set=None,
                           after_set=None,
                           sequence='sequential',
                           think_time=500,
                           verbosity='debug',
                           variables={}):
    """Return a `TestRunner` base class that runs ``.webtest`` files in the
    given list of `~webtest.runner.TestSet`\s, and does correlation of request
    parameters with responses.

    All arguments to this function have the same meaning as their counterparts
    in `~webtest.runner.get_test_runner`, with the possible exception of
    ``verbosity``--the correlating runner is more verbose, printing certain
    output about found correlations regardless of the ``verbosity`` setting.
    """
    WebtestRunner.set_class_attributes(test_sets,
        before_set, after_set, sequence, think_time, verbosity)

    # Define the actual TestRunner wrapper class. This allows us to delay
    # instantiation of the class until the Grinder threads run, while still
    # populate the instance with the given variables in the __init__ method.
    class TestRunner (CorrelationRunner):
        def __init__(self):
            """Create a TestRunner instance initialized with the given
            variables.
            """
            CorrelationRunner.__init__(self, **variables)

    # Return the class (NOT an instance!)
    return TestRunner


