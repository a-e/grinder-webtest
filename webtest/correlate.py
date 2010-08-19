# correlate.py

"""Correlating requests and responses

It would be nice to have a partially automated method of correlating webtest
request parameters with any values that might be getting returned by responses
leading up to that request.

When running in correlation mode, each request is examined. For each parameter
name sent with the request, search in the response body of the preceding
requests. This doesn't have to be too intelligent; for instance, if a request
contains a parameter named "SID", look in prior responses to see if they
contain the text "SID"

If a name-based search fails, try a value-based search. This is probably less
likely to work, especially in the case of parameters that change with each run
(like SID), but for others it may yield results if the response does not
actually contain the exact parameter name.

The action to take after finding correlated parameters can vary; a simple
solution would be to just print out the portion of the response that matched,
with some surrounding context. An ideal solution would be automatic
parameterization of the .webtest file, and automatic insertion of Capture
expressions that could later be customized (since automatic regular expression
inference would be pretty much unsolvable without some knowledge of the
response format).

How to tackle this? Well, maybe it'd be good to start with a TestRunner
that is specialized for correlation. The TestRunner should not modify the
original .webtest files, but instead write out a copy with the inferred
correlations. Maybe a good approach would be to simply add comments to
a copy of the .webtest file.

The TestRunner will need to keep track of the full response body of
each request, and may require a more foolproof way of identifying
responses (more human-readable, that is, rather than just by index).

Leverage as much of the existing webtest parser/runner code as possible.
"""
__docformat__ = 'restructuredtext en'

from runner import WebtestRunner
from net.grinder.script.Grinder import grinder
log = grinder.logger.output


class CorrelationRunner (WebtestRunner):
    """A WebtestRunner that correlates requests and responses.
    """
    def __init__(self, **variables):
        WebtestRunner.__init__(self, **variables)
        # Dict of lists of HTTPResponses, indexed by webtest filename
        self.webtest_responses = {}


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
                           before_set=None, after_set=None,
                           sequence='sequential', think_time=500, variables={}):
    """Return a TestRunner base class that runs .webtest files in the given
    test_sets, and does correlation of request parameters with responses.
    """
    WebtestRunner.set_class_attributes(test_sets,
        before_set, after_set, sequence, think_time, 'debug')

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


