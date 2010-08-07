# runner.py

"""Provides a base class for creating Grinder TestRunners that execute
requests in Visual Studio ``.webtest`` files.

This module provides one high-level function called `get_test_runner`, which
creates a `TestRunner` class (that's a class, not an instance). At minimum,
this function takes a nested list of ``.webtest`` files to execute. Call this
from your main Grinder script like so::

    from webtest.runner import get_test_runner

    my_tests = [['my_test.webtest']]
    TestRunner = get_test_runner(my_tests)

It's assumed that you will eventually have more than one ``.webtest`` file to
execute, which is why the first argument is a list. But why is it a nested
list? Well, because you may have several ``.webtest`` files that must be run
sequentially, in a single `TestRunner` instance. For example, if you have two
different "test sets", each with two ``.webtest`` files, you could create your
TestRunner like this::

    my_test_sets = [
        ['invoice_1.webtest', 'invoice_2.webtest'],
        ['billing_1.webtest', 'billing_2.webtest'],
    ]
    TestRunner = get_test_runner(my_test_sets)

The default behavior is for each `TestRunner` instance (each Grinder worker
thread, that is) to run all of the tests in sequential order. But perhaps
you want the first thread to run the 'invoice' tests, and the second thread
to run the 'billing' tests. That's easy, just pass 'thread' as the second
argument to `get_test_runner`::

    TestRunner = get_test_runner(my_test_sets, 'thread')

Now, if you run two threads, then each thread will run a different sub-list
of ``my_test_sets``. If you have more than two threads, then the extra threads
will be assigned test sets starting over at the beginning:

    - Thread 0: invoice
    - Thread 1: billing
    - Thread 2: invoice
    - Thread 3: billing
    - ...

A third option is to use random sequencing, so that each thread will choose
a random test set to run::

    TestRunner = get_test_runner(my_test_sets, 'random')

With this, you might end up with something like:

    - Thread 0: billing
    - Thread 1: billing
    - Thread 2: invoice
    - Thread 3: billing
    - Thread 4: invoice
    - ...

There are two critically important things that are often needed in web
application testing--parameterization, and capturing of responses. These are
handled by the inclusion of variables. To use variables, you must first
determine which parts of your ``.webtest`` file need to be parameterized.
Typically, you will parameterize the ``Value`` attribute of some element, for
instance::

    <FormPostParameter Name="UID" Value="wapcaplet" />
    <FormPostParameter Name="PWD" Value="W0nderPet$" />

To turn this into a parameter, insert an ``ALL_CAPS`` name surrounded by curly
braces in place of the ``Value`` attribute's value::

    <FormPostParameter Name="UID" Value="{USERNAME}" />
    <FormPostParameter Name="PWD" Value="{PASSWORD}" />

Then, define values for these variables when you call `get_test_runner`, by
passing a dictionary::

    my_vars = {
        'USERNAME': 'wapcaplet',
        'PASSWORD': 'W0nderPet$',
    }
    TestRunner = get_test_runner(my_test_sets, variables=my_vars)

Variable values can also be set directly in the ``.webtest`` file itself. See the
`WebtestRunner.eval_expressions` method below for details.

Variables can also be set to the result of a "macro"; this is useful if you
need to refer to the current date (when the script runs), or for generating
random alphanumeric values::

    <FormPostParameter Name="INVOICE_DATE" Value="{today(%y%m%d}"/>
    <FormPostParameter Name="INVOICE_ID" Value="{random_digits(10)}"/>

See the `macro` method below for details.

If you need to set a variable's value from one of the HTTP responses in your
``.webtest``, you can use a capture expression. For example, you may need to
capture a session ID as it comes back from the login request, so that you can
use it in subsequent requests. To do that, include a ``<Capture>...</Capture>``
element somewhere in the ``<Request...>`` tag. The ``Capture`` element can
appear anywhere inside the ``Request`` element, though it makes the most
chronological sense to put it at the end::

    <Request Method="POST" Url="http://my.site/login" ...>
        ...
        <Capture>
            <![CDATA[{SESSION_ID = <sid>(.+)</sid>}]]>
        </Capture>
    </Request>

This will look for ``<sid>...</sid>`` in the response body, and set the
variable ``SESSION_ID`` equal to its contents. You capture an arbitrary number
of variable values in this way, then refer to them later in the ``.webtest``
file (or even in subsequent ``.webtest`` files in the same test set). See the
`WebtestRunner.eval_capture` method below for additional details.

"""

# Everything in this script should be compatible with Jython 2.2.1.

import random
import datetime

# Import the webtest parser
import parser

# Import the necessary Grinder stuff
# This is wrapped with exception handling, to allow Sphinx to import this
# module for documentation purposes
try:
    from net.grinder.script import Test
    from net.grinder.script.Grinder import grinder
    from net.grinder.plugin.http import HTTPPluginControl, HTTPRequest
    from HTTPClient import NVPair
except ImportError:
    print("Grinder module import failed.")
    print("You may need to add grinder.jar to your classpath.")
    print("Continuing blissfully onward...")
else:
    # Convenient access to logger
    log = grinder.logger.output

    # Set default headers for all connections
    connectionDefaults = HTTPPluginControl.getConnectionDefaults()
    connectionDefaults.defaultHeaders = [
        NVPair('Accept-Language', 'en-us'),
        NVPair('User-Agent',
               'Mozilla/4.0 (compatible; '
               'MSIE 7.0; '
               'Windows NT 5.1; '
               '.NET CLR 1.1.4322; '
               '.NET CLR 2.0.50727; '
               '.NET CLR 3.0.4506.2152; '
               '.NET CLR 3.5.30729)'),
        NVPair('Accept', '*/*'),
    ]


def macro(macro_name, args):
    """Expand a macro and return the result.

    Supported macros:

        random_digits(num)
            Generate a random num-digit string
        random_letters(num)
            Generate a random num-character string of letters
        random_alphanumeric(num)
            Generate a random num-character alphanumeric string
        today(format)
            Return today's date in the given format. For example,
            ``%m%d%y`` for ``MMDDYY`` format. See the datetime_
            module documentation for allowed format strings.
        today_plus(days, format)
            Return today plus some number of days, in the given format.

    .. _datetime: http://docs.python.org/library/datetime.html
    """
    def _sample(choices, how_many):
        """Return `how_many` randomly-chosen items from `choices`.
        """
        return [random.choice(choices) for x in range(how_many)]

    if macro_name == 'random_digits':
        return ''.join(_sample('0123456789', int(args)))

    elif macro_name == 'random_letters':
        return ''.join(_sample('ABCDEFGHIJKLMNOPQRSTUVWXYZ', int(args)))

    elif macro_name == 'random_alphanumeric':
        return ''.join(_sample('0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ', int(args)))

    elif macro_name == 'today':
        return datetime.date.today().strftime(args)

    elif macro_name == 'today_plus':
        days, format = [arg.strip() for arg in args.split(',')]
        return (datetime.date.today() + datetime.timedelta(int(days))).strftime(format)

    else:
        raise NameError("Unknown macro: %s" % macro_name)


class WebtestRunner:
    """A base class for `TestRunner` instances that will run ``.webtest`` files.

    **NOTE**: This class is not meant to be instantiated or overridden
    directly--use the `get_test_runner` function instead.
    """
    # CLASS ATTRIBUTES AND METHODS
    # ----------------------------------------------
    # The list of webtests, and the corresponding requests, are class
    # attributes; all worker threads share the same wrapped HTTPRequests,
    # and the same webtest.Request instances.

    # Print debugging output
    debug = False

    # List of lists of .webtest filenames
    webtest_sets = []
    # Lists of .webtest files to run before and after each test set
    before_set = []
    after_set = []
    # Sequencing (sequential, random, or thread)
    sequence = 'sequential'
    # Dict of lists of requests, indexed by .webtest filename
    webtest_requests = {}
    # Time to sleep between requests
    think_time = 500
    # Verbosity of logging
    verbosity = 'quiet'

    # Sequential test numbers, so each request gets a unique number
    # Each webtest's requests will be numbered sequentially starting with
    # this number; the next webtest will start at test_number + test_number_skip
    test_number = 1000
    # How much to increment the test_number for each test
    # (this is the maximum number of requests that may be in a single webtest)
    test_number_skip = 1000


    def add_webtest_file(cls, filename):
        """Add all requests in the given ``.webtest`` filename to the class.
        """
        # Parse the Webtest file
        webtest = parser.Webtest(filename)
        # Create an HTTPRequest and Test wrapper for each request,
        # numbered sequentially
        test_requests = []
        for index, request in enumerate(webtest.requests):
            # First request is test_number+1, then test_number+2 etc.
            test = Test(cls.test_number + index + 1, str(request))
            wrapper = test.wrap(HTTPRequest())
            test_requests.append((test, wrapper, request))
        # Add the (test, request) list to class for this filename
        cls.webtest_requests[filename] = test_requests
        # Skip ahead to the next test_number
        cls.test_number += cls.test_number_skip
    # Make this a class method
    add_webtest_file = classmethod(add_webtest_file)


    def set_class_attributes(cls, before_set, webtest_sets, after_set,
                             sequence='sequential',
                             think_time=500,
                             verbosity='quiet'):
        """Set attributes that affect all `WebtestRunner` instances.

        before_set
            A list of webtests that should be run before each test set.
            Use this if all webtests need to perform the same initial
            steps, such as logging in.

        webtest_sets
            A list of lists, where each inner list contains one or more
            webtests that must be run sequentially. Each inner list of
            webtests will run in a single TestRunner instance, ensuring
            that they can share variable values.

        after_set
            A list of webtests that should be run after each test set.
            Use this if all webtests need to perform the same final
            steps, such as logging out.

        sequence
            How to run the given test sets. Allowed values:

            'sequential'
                Each thread runs all test sets in order.
            'random'
                Each thread runs a random test set for each ``__call__``.
            'thread'
                Thread 0 runs the first test set, Thread 1 runs the next, and
                so on. If there are fewer threads than test sets, some test
                sets will not be run.  If there are more threads than test
                sets, the extra threads start over at 0 again.

        think_time
            Time in milliseconds to sleep between each request.

        verbosity
            How chatty to be when logging. May be:

            'debug'
                Everything, including response body
            'info'
                Basic info, including request parameters and evaluated
                expressions
            'quiet'
                Minimal info, including .webtest filename and test names
            'error'
                Only log errors, nothing else

        """
        # Ensure that webtest_sets is a list
        if not isinstance(webtest_sets, list):
            raise ValueError("webtest_sets must be a list of lists.")
        # Ensure that each item in the list is also a list
        for webtest_set in webtest_sets:
            if not isinstance(webtest_set, list):
                raise ValueError("webtest_sets must be a list of lists.")
        # Ensure that sequence matches allowed values
        if sequence not in ('sequential', 'random', 'thread'):
            raise ValueError("sequence must be 'sequential', 'random', or 'thread'.")
        # Ensure that verbosity is valid
        if verbosity not in ('debug', 'info', 'quiet', 'error'):
            raise ValueError("verbosity must be 'debug', 'info', 'quiet', or 'error'.")

        # Set the webtest filename and think time at the class level
        cls.before_set = before_set
        cls.webtest_sets = webtest_sets
        cls.after_set = after_set
        cls.sequence = sequence
        cls.think_time = think_time
        cls.verbosity = verbosity
        # Empty the list of test set requests
        cls.test_set_requests = {}

        # Add each webtest in the after_set
        for filename in before_set:
            cls.add_webtest_file(filename)
        # Add each webtest set to the class
        for webtest_set in webtest_sets:
            # Add all filenames in this set to the class
            for filename in webtest_set:
                cls.add_webtest_file(filename)
        # Add each webtest in the after_set
        for filename in after_set:
            cls.add_webtest_file(filename)
    # Make this a class method
    set_class_attributes = classmethod(set_class_attributes)


    # INSTANCE ATTRIBUTES AND METHODS
    # ----------------------------------------------

    def __init__(self, **variables):
        """Create a WebtestRunner instance, and run tests in the before_set.
        """
        # Dictionary of instance variables, indexed by name
        self.variables = variables

        # Run tests in the before_set
        self.run_webtest_set(WebtestRunner.before_set)


    def __del__(self):
        """Destructor--run tests in the after_set.
        """
        # Run tests in the after_set
        self.run_webtest_set(WebtestRunner.after_set)


    def eval_expressions(self, value):
        """Parse the given string for variables or macros, and do any necessary
        variable assignment. Return the string with all expressions expanded.

        Allowed expressions:

            ``{MY_VAR}``
                Expand to the current value of ``MY_VAR``
            ``{MY_VAR = literal}``
                Assign ``MY_VAR`` a literal value, and expand to that value
            ``{macro_name(args)}``
                Expand to the result of ``macro_name(args)``
            ``{MY_VAR = macro_name(args)}``
                Assign ``MY_VAR`` the result of calling ``macro_name(args)``,
                and also expand to the resulting value. See the `macro`
                method for available macros.

        Any given value that does not match any of these forms is simply
        returned as-is.

        The given value may contain multiple ``{...}`` expressions, and may have
        additional text before or after any expression. For example, if you
        have previously assigned two variables ``FOO`` and ``BAR``:

            >>> eval_expressions('{FOO = Hello}')
            'Hello'
            >>> eval_expressions('{BAR = world}')
            'world'

        you can combine them in an expression like this:

            >>> eval_expressions('{FOO} {BAR}!')
            'Hello world!'

        The only caveat is that a ``{...}`` expression may not contain another
        ``{...}`` expression inside it.
        """
        # Regular expressions to match in eval_expressions
        # Import re here to avoid threading problems
        # See: http://osdir.com/ml/java.grinder.user/2003-07/msg00030.html
        import re
        # Match the first {...} expression
        re_expansion = re.compile('([^{]*){([^}]+)}(.*)')
        # VAR_NAME=macro(args)
        re_var_macro = re.compile('([_A-Z0-0-99]+) ?= ?([_a-z]+)\(([^)]*)\)')
        # VAR_NAME=literal
        re_var_literal = re.compile('([_A-Z0-9]+) ?= ?([^}]+)')
        # macro(args)
        re_macro = re.compile('([_a-z]+)\(([^)]*)\)')
        # VAR_NAME
        re_var = re.compile('([_A-Z0-9]+)')

        # Match and replace until no {...} expressions are found
        to_expand = re_expansion.match(value)
        while to_expand:
            before, expression, after = to_expand.groups()

            # VAR_NAME=macro(args)
            if re_var_macro.match(expression):
                name, macro_name, args = re_var_macro.match(expression).groups()
                expanded = self.variables[name] = macro(macro_name, args)

            # VAR_NAME=literal
            elif re_var_literal.match(expression):
                name, literal = re_var_literal.match(expression).groups()
                self.variables[name] = literal
                expanded = literal

            # macro(args)
            elif re_macro.match(expression):
                macro_name, args = re_macro.match(expression).groups()
                expanded = macro(macro_name, args)

            # VAR_NAME
            elif re_var.match(expression):
                name = re_var.match(expression).groups()[0]
                if name in self.variables:
                    expanded = self.variables[name]
                else:
                    raise NameError("Variable '%s' is not initialized!" % name)

            # Unknown
            else:
                raise SyntaxError(
                  "Syntax error '%s' in value '%s'" % (expression, value))

            if WebtestRunner.verbosity in ('debug', 'info'):
                log("%s => '%s'" % (expression, expanded))

            # Assemble the expanded value and check for another match
            value = before + expanded + after
            to_expand = re_expansion.match(value)

        return value


    def eval_capture(self, request, response):
        """Evaluate any ``Capture`` expressions in the given request, and set
        variables to matching text in the given response.

        In order for this to work, you should include a ``Capture`` element
        inside the ``Request`` element whose response you want to capture. Each
        expression inside ``Capture`` should follow this format::

            {VAR_NAME = regexp}

        Where ``regexp`` is a regular expression with parentheses around the
        part you want to capture (or no parentheses to capture the entire
        match).  For example, if your response contains::

            ... <a href="http://python.org"> ...

        And you want to store the URL into a variable called ``HREF``, do::

            {HREF = <a href="([^"]+)">}

        If any capture expression is not found in the response, a `RuntimeError`
        is raised. This makes them useful for verification too--if you want to
        ensure that a response contains expected text, just include a capture
        expression that looks for it. In this case, you can leave out the
        parentheses, since you don't need to capture any particular part, and
        if you don't need to keep the value for later, you can just assign it
        to a dummy variable.

        For example, to verify that the response includes a form with a
        "submit" button::

            {VERIFY = <form.*>.*<input type="submit".*>.*</form>}

        You can include multiple ``{VAR_NAME = regexp}`` expressions in the same
        ``Capture`` element, to capture several variables from the same response,
        or to do several verifications.

        Since regular expressions often contain characters that are precious to
        XML, such as ``< > &`` and so on, you can enclose your capture expressions
        in a ``CDATA`` block to prevent them from being interpreted as XML::

            <Request ...>
                ...
                <Capture>
                    <![CDATA[
                        {VAR_A = <a href="([^"]+)">}
                        {VAR_B = <b>([^<]+)</b>)}
                    ]]>
                </Capture>
            </Request>

        You can include ``{VAR_NAME}`` references in the right-hand side of the
        expression; for example, if you have previously assigned a value to
        ``ORDER_NUMBER``, and you want to capture the contents of a ``div``
        having that order number as its ``id``, you could do::

            {ORDER_DIV = <div id="{ORDER_NUMBER}">(.*)</div>}

        If ``ORDER_NUMBER`` was previously set to ``12345``, then the above
        will be expanded to::

            {ORDER_DIV = <div id="12345">(.*)</div>}

        before matching in the response body.
        """
        # If capture expression is empty, there's nothing to do
        if request.capture.strip() == '':
            return

        # Import re here to avoid threading problems
        # See: http://osdir.com/ml/java.grinder.user/2003-07/msg00030.html
        import re
        # Match a {VAR_NAME = <regular expression>}
        re_capture = re.compile('^{([_A-Z0-9]+) ?= ?(.+)}$')

        # Get response body
        body = response.getText()
        # Evaluate each {...} expression found in the list of request.captures()
        for expression in request.captures():
            # Error if this expression doesn't look like a capture
            match = re_capture.search(expression)
            if not match:
                raise SyntaxError("Syntax error in capture expression '%s'" % \
                                  expression)

            # Get the two parts of the capture expression
            name, value = match.groups()
            # Expand any {VAR} expressions before evaluating the regexp
            regexp = self.eval_expressions(value)

            if WebtestRunner.verbosity in ('debug', 'info'):
                log("Looking in response for match to regexp: %s" % regexp)

            # Error if the regexp doesn't match part of the response body
            match = re.search(regexp, body)
            if not match:
                log("!!!!!! No match for %s" % regexp)
                log("!!!!!! Response body:")
                log(body)
                raise RuntimeError("No match for %s" % regexp)

            # Set the given variable name to the first parenthesized expression
            if match.groups():
                value = match.group(1)
            # or the entire match if there was no parenthesized expression
            else:
                value = match.group(0)
            if WebtestRunner.verbosity in ('debug', 'info'):
                log("Captured %s = %s" % (name, value))
            self.variables[name] = value


    def execute(self, test, wrapper, request):
        """Execute a Grinder `Test` instance, wrapped in ``wrapper``, that
        sends a `~webtest.parser.Request`.
        """
        if WebtestRunner.verbosity != 'error':
            log("------ Test %d: %s" % (test.getNumber(), request))

        # Evaluate any expressions in the request URL
        url = self.eval_expressions(request.url)
        # Expand/assign any variables in the request parameters,
        # and convert to NVPairs
        parameters = []
        for name, value in request.parameters:
            value = self.eval_expressions(value)
            pair = NVPair(name, value)
            parameters.append(pair)
        # Convert headers to NVPairs
        headers = [NVPair(name, value) for (name, value) in request.headers]

        # Send a POST or GET to the wrapped HTTPRequest
        if request.method == 'POST':
            # If the request has a body, use that
            if request.body:
                body = self.eval_expressions(request.body)
                response = wrapper.POST(url, body, headers)
            # Otherwise, pass the form parameters
            else:
                response = wrapper.POST(url, parameters, headers)

        elif request.method == 'GET':
            response = wrapper.GET(url, parameters, headers)

        else:
            raise ValueError("Unknown HTTP method: %s" % request.method)

        if WebtestRunner.verbosity == 'debug':
            # Log the response
            body = response.getText()
            # Prettify xml
            if body.startswith('<?xml'):
                # This helps with making the XML more readable, but gets UTF-8
                # errors from time to time. If they occur, ignore them and just
                # skip prettification
                import xml.dom.minidom
                try:
                    body = body.replace('\n', '').replace('\r', '').replace('\t', '')
                    body = xml.dom.minidom.parseString(body).toprettyxml()
                except:
                    pass
            log("------ Response from %s: ------" % request)
            log(body)

        # If request has a 'Capture' attribute, parse it
        if request.capture:
            self.eval_capture(request, response)

        return response


    def run_webtest_set(self, webtest_set):
        """Run all ``.webtest`` files in the given ``webtest_set``.
        """
        for filename in webtest_set:
            if WebtestRunner.verbosity != 'error':
                log("==== Executing: %s ==========" % filename)

            # Execute all requests in this test set, in order
            for test, wrapper, request in WebtestRunner.webtest_requests[filename]:
                # Execute this request
                try:
                    response = self.execute(test, wrapper, request)
                # If problems occurred, report an error and re-raise
                except RuntimeError:
                    grinder.statistics.forLastTest.success = False
                    raise

                # If response was not valid, report an error
                if response.getStatusCode() >= 400:
                    grinder.statistics.forLastTest.success = False

                # Sleep
                grinder.sleep(WebtestRunner.think_time)


    def __call__(self):
        """Execute all requests according to the class attribute ``sequence``,
        waiting ``think_time`` between each request.
        """
        # Delay reporting, to allow potential errors to be reported
        grinder.statistics.delayReports = True

        # Determine which sequencing to use
        sequence = WebtestRunner.sequence
        # Run a single webtest_set at random.
        if sequence == 'random':
            webtest_set = random.choice(WebtestRunner.webtest_sets)
            self.run_webtest_set(webtest_set)

        # Run a single webtest_set based on the current thread number.
        elif sequence == 'thread':
            index = grinder.getThreadNumber() % len(WebtestRunner.webtest_sets)
            webtest_set = WebtestRunner.webtest_sets[index]
            self.run_webtest_set(webtest_set)

        # Run all webtest_sets sequentially.
        else: # assume 'sequential'
            for webtest_set in WebtestRunner.webtest_sets:
                self.run_webtest_set(webtest_set)


def get_test_runner(before_set, webtest_sets, after_set,
                    sequence='sequential', think_time=500, variables={},
                    verbosity='quiet'):
    """Return a `TestRunner` base class that runs ``.webtest`` files in the
    given ``webtest_sets``.

        variables
            Default variables for all `TestRunner` instances. Each
            `TestRunner` instance will get their own copy of these, but
            passing them here lets you define defaults for commonly-used
            variables like server name, username, or password.

    See `WebtestRunner.set_class_attributes` for documentation on the other
    parameters.
    """
    WebtestRunner.set_class_attributes(before_set, webtest_sets, after_set,
        sequence, think_time, verbosity)

    # Define the actual TestRunner wrapper class. This allows us to delay
    # instantiation of the class until the Grinder threads run, while still
    # populate the instance with the given variables in the __init__ method.
    class TestRunner (WebtestRunner):
        def __init__(self):
            """Create a TestRunner instance initialized with the given
            variables.
            """
            WebtestRunner.__init__(self, **variables)

    # Return the class (NOT an instance!)
    return TestRunner


