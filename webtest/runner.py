# runner.py

"""This module provides a high-level function called `get_test_runner`, which
creates a `WebtestRunner` class for executing Visual Studio ``.webtest`` files
found in one or more `TestSet`\s.


Test Sets and Test Runners
--------------------------

In order to execute a ``.webtest`` file, you must wrap it in a `TestSet`, then
create a `WebtestRunner` class via the `get_test_runner` function. Here is a
simple example::

    from webtest.runner import TestSet, get_test_runner

    my_tests = [TestSet('my_test.webtest')]
    TestRunner = get_test_runner(my_tests)

Each `TestSet` in the list will be executed by a single `WebtestRunner` instance.
If you have more than one ``.webtest`` file to execute, you can pass all the
filenames to a single `TestSet`::

    my_tests = [TestSet('test1.webtest', 'test2.webtest', 'test3.webtest')]
    TestRunner = get_test_runner(my_tests)

The above example would run three tests in sequential order, in the same
`WebtestRunner` instance. This is recommended if there are dependencies between
the tests (either they must always run in a given sequence, or there are
captured variables shared between them--more on this shortly).

Another way would be to create a separate `TestSet` instance for each test::

    my_tests = [
        TestSet('test1.webtest'),
        TestSet('test2.webtest'),
        TestSet('test3.webtest'),
    ]
    TestRunner = get_test_runner(my_tests)

Here, each ``.webtest`` could be run in a separate `WebtestRunner` instance,
and not necessarily in sequential order. You might take this approach if all
three tests are independent, and have no need of running in sequence or sharing
variables.

The `TestSet` might also be used for logical grouping of related tests. For
example, if you have some tests for invoicing, and others for billing, you
might create your TestRunner like this::

    my_tests = [
        TestSet('invoice_1.webtest', 'invoice_2.webtest'),
        TestSet('billing_1.webtest', 'billing_2.webtest'),
    ]
    TestRunner = get_test_runner(my_tests)

Here again, the two invoice tests will be run in order, in the same
`WebtestRunner` instance, and the two billing tests will also be run in order,
in the same `WebtestRunner` instance.

This covers the essentials of using this module; the next sections deal with
how to initialize and capture variable values, and how to control the execution
sequence.


Parameterization and Capturing
------------------------------

There are two critically important things that are often needed in web
application testing: parameterization of values, and capturing of responses.
These are handled by the inclusion of variables. To use variables, you must
first determine which parts of your ``.webtest`` file need to be parameterized.
Typically, you will parameterize the ``Value`` attribute of some element, for
instance::

    <FormPostParameter Name="UID" Value="wapcaplet" />
    <FormPostParameter Name="PWD" Value="W0nderPet$" />

To turn these into parameters, insert an ``ALL_CAPS`` name surrounded by curly
braces in place of the ``Value`` attribute's value::

    <FormPostParameter Name="UID" Value="{USERNAME}" />
    <FormPostParameter Name="PWD" Value="{PASSWORD}" />

Then, define values for these variables when you call `get_test_runner`, by
passing a dictionary using the ``variables`` keyword::

    my_vars = {
        'USERNAME': 'wapcaplet',
        'PASSWORD': 'W0nderPet$',
    }
    TestRunner = get_test_runner(my_tests, variables=my_vars)

Variables do not have a particular type; all variables are treated as strings,
and must be defined as such in the ``variables`` dictionary.

This is just one way to set variable values, and would normally be used to
initialize "global" variables that are used throughout all of your ``.webtest``
files. You may also initialize "local" variables in a single ``.webtest`` file
by simply assigning the ``ALL_CAPS`` variable name a literal value when it is
first referenced::

    <FormPostParameter Name="INVOICE_ID" Value="{INVOICE_ID = 12345}" />

Here, ``INVOICE_ID`` is set to the value ``12345``; any later reference to
``INVOICE_ID`` in the same ``.webtest`` file (or in other ``.webtest`` files
that come later in the same `TestSet`) will evaluate to ``12345``. See the
`WebtestRunner.eval_expressions` method below for details.

Variables can also be set to the result of a "macro"; this is useful if you
need to refer to the current date (when the script runs), or for generating
random alphanumeric values::

    <FormPostParameter Name="INVOICE_DATE" Value="{TODAY = today(%y%m%d}"/>
    <FormPostParameter Name="INVOICE_ID" Value="{INVOICE_ID = random_digits(10)}"/>

See the `macro` method below for details.

Finally, and perhaps most importantly, if you need to set a variable's value
from one of the HTTP responses in your ``.webtest``, you can use a capture
expression. For example, you may need to capture a session ID as it comes back
from the login request, so that you can use it in subsequent requests. To do
that, include a ``<Capture>...</Capture>`` element somewhere in the
``<Request...>`` tag. The ``Capture`` element can appear anywhere inside the
``Request`` element, though it makes the most chronological sense to put it at
the end::

    <Request Method="POST" Url="http://my.site/login" ...>
        ...
        <Capture>
            <![CDATA[{SESSION_ID = <sid>(.+)</sid>}]]>
        </Capture>
    </Request>

This will look for ``<sid>...</sid>`` in the response body, and set the
variable ``SESSION_ID`` equal to its contents. You capture an arbitrary number
of variable values in this way, then refer to them later in the ``.webtest``
file (or in subsequent ``.webtest`` files in the same `TestSet`). See the
`WebtestRunner.eval_capture` method below for additional details.


Sequencing
----------

When calling `get_test_runner`, you can use the ``sequence`` keyword to control
how the tests are executed. Using the same example as above::

    my_tests = [
        TestSet('invoice_1.webtest', 'invoice_2.webtest'),
        TestSet('billing_1.webtest', 'billing_2.webtest'),
    ]

The default behavior is for each `WebtestRunner` instance (each Grinder worker
thread, that is) to run all of the tests in sequential order. This is the same
as passing ``sequence='sequential'``::

    TestRunner = get_test_runner(my_tests, sequence='sequential')

and would give this runtime behavior:

* Thread 0: invoice, billing
* Thread 1: invoice, billing
* ...

But perhaps you want the first thread to run the invoice tests, and the second
thread to run the billing tests. To do this, pass ``sequence='thread'`` to
`get_test_runner`::

    TestRunner = get_test_runner(my_tests, sequence='thread')

Now, if you run two threads, then the first thread will run the first
`TestSet`, and the second thread will run the second `TestSet`. If you have
more than two threads, then the extra threads will cycle through the list of
available `TestSet`\s again:

* Thread 0: invoice
* Thread 1: billing
* Thread 2: invoice
* Thread 3: billing
* ...

Another option is to use random sequencing, so that each thread will choose
a random `TestSet` to run::

    TestRunner = get_test_runner(my_tests, sequence='random')

With this, you might end up with something like:

* Thread 0: billing
* Thread 1: billing
* Thread 2: invoice
* Thread 3: billing
* Thread 4: invoice
* ...

Finally, it's possible to assign a "weight" to each `TestSet`; this is similar
to random sequencing, except that it allows you to control how often each each
`TestSet` is run in relation to the others. For example, if you would like to
run the billing tests three times as often as the invoice tests::

    my_tests = [
        TestSet('invoice_1.webtest', 'invoice_2.webtest', weight=1),
        TestSet('billing_1.webtest', 'billing_2.webtest', weight=3),
    ]
    TestRunner = get_test_runner(my_tests, sequence='weighted')

The ``weight`` of each `TestSet` can be any numeric value; you might use
integers to obtain a relative frequency, like the example above, or you might
use floating-point values to define a percentage. Here's the above example
using percentages::

    my_tests = [
        TestSet('invoice_1.webtest', 'invoice_2.webtest', weight=0.25),
        TestSet('billing_1.webtest', 'billing_2.webtest', weight=0.75),
    ]
    TestRunner = get_test_runner(my_tests, sequence='weighted')

In other words, the invoice tests will be run 25% of the time, and the billing
tests 75% of the time. In this case, you might end up with the following:

* Thread 0: billing
* Thread 1: billing
* Thread 2: invoice
* Thread 3: billing
* ...

As with random sequencing, each thread will choose a `TestSet` at random, with
the likelihood of choosing a particular `TestSet` being determined by the
weight. This allows you to more closely mimic a real-world distribution of
activity among your various test scenarios.


Before and After
----------------

If you have test steps that must be run at the beginning of testing (such as
logging into the application), and/or steps that must be run at the end (such
as logging out), you can encapsulate those in `TestSet`\s and pass them using
the ``before_set`` and ``after_set`` keywords. For example::

    login = TestSet('login.webtest')
    logout = TestSet('logout.webtest')
    TestRunner = get_test_runner(my_tests, before_set=login, after_set=logout)

The ``before_set`` will be run when a `WebtestRunner` instance is created
(normally when the Grinder worker thread starts up), and the ``after_set`` will
be run when the instance is destroyed (the thread finishes execution, or is
interrupted).

"""

# Everything in this script should be compatible with Jython 2.2.1.

import random
import datetime

# Import the webtest parser
import parser
import macro

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
    from stub import Test, NVPair, HTTPRequest, grinder, log
else:
    # Convenient access to logger
    log = grinder.logger.output

    # Set default headers for all connections
    connectionDefaults = HTTPPluginControl.getConnectionDefaults()
    connectionDefaults.setTimeout(60000)
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


class TestSet:
    """A collection of ``.webtest`` files that are executed sequentially, with
    an implied dependency between them.

        ``webtest_filenames``
            One or more ``.webtest`` XML filenames of tests to run together
            in this set

    Optional keyword arguments:

        ``weight``
            A numeric indicator of how often to run this `TestSet`.
            Use this with the ``sequence='weighted'`` argument to
            `get_test_runner`.

    """
    def __init__(self, *webtest_filenames, **kwargs):
        """Create a TestSet.
        """
        self.filenames = list(webtest_filenames)
        self.weight = kwargs.get('weight', 1.0)


class CaptureFailed (RuntimeError):
    """Raised when a capture expression is not matched."""
    pass


class WebtestRunner:
    """A base class for ``TestRunner`` instances that will run `TestSet`\s.

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

    # List of TestSets, each containing .webtest filenames
    test_sets = []
    # TestSets to run before and after each test set
    before_set = None
    after_set = None
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


    def _add_webtest_file(cls, filename):
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
    _add_webtest_file = classmethod(_add_webtest_file)


    def set_class_attributes(cls,
                             test_sets,
                             before_set=None,
                             after_set=None,
                             sequence='sequential',
                             think_time=500,

                             verbosity='quiet',
                             macro_class=macro.Macro):
        """Set attributes that affect all `WebtestRunner` instances.

        ``test_sets``
            A list of TestSets, where each `TestSet` contains one or more
            webtests that must be run sequentially. Each `TestSet`
            will run in a single TestRunner instance, ensuring
            that they can share variable values.

        ``before_set``
            A `TestSet` that should be run when the `TestRunner` is
            initialized. Use this if all webtests need to perform the same
            initial steps, such as logging in.

        ``after_set``
            A `TestSet` that should be run when the `TestRunner` is destroyed.
            Use this if all webtests need to perform the same final steps, such
            as logging out.

        ``sequence``
            How to run the given test sets. Allowed values:

            'sequential'
                Each thread runs all TestSets in order.
            'random'
                Each thread runs a random TestSet for each ``__call__``.
            'weighted'
                Each thread runs a random TestSet, with those having a
                larger ``weight`` being run more often.
            'thread'
                Thread 0 runs the first TestSet, Thread 1 runs the next, and so
                on. If there are fewer threads than TestSets, some TestSets
                will not be run. If there are more threads than TestSets, the
                extra threads start over at 0 again.

        ``think_time``
            Time in milliseconds to sleep between each request.

        ``verbosity``
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

        ``macro_class``
            The class where macro functions are defined. Uses the standard
            `~webtest.macro.Macro` class by default; pass a derived class
            if you want to define your own macros.

        """
        # Type-checking
        # Ensure that test_sets is a list
        if not isinstance(test_sets, list):
            raise ValueError("test_sets must be a list of TestSets.")
        # Ensure that each item in the list is a TestSet
        for test_set in test_sets:
            if not isinstance(test_set, TestSet):
                raise ValueError("test_sets must be a list of TestSets.")
        # If before_set was provided, ensure it is a TestSet
        if before_set and not isinstance(before_set, TestSet):
            raise ValueError("before_set must be a TestSet.")
        # If after_set was provided, ensure it is a TestSet
        if after_set and not isinstance(after_set, TestSet):
            raise ValueError("after_set must be a TestSet.")
        # Ensure that sequence matches allowed values
        if sequence not in ('sequential', 'random', 'weighted', 'thread'):
            raise ValueError("sequence must be 'sequential', 'random', 'weighted', or 'thread'.")
        # Ensure that verbosity is valid
        if verbosity not in ('debug', 'info', 'quiet', 'error'):
            raise ValueError("verbosity must be 'debug', 'info', 'quiet', or 'error'.")
        # Ensure that macro_class is a class, and is derived from macro.Macro
        if not (type(macro_class) == type(macro.Macro) and issubclass(macro_class, macro.Macro)):
            raise ValueError("macro_class must be a subclass of webtest.macro.Macro")

        # Initialize all class variables
        cls.test_sets = test_sets
        cls.before_set = before_set
        cls.after_set = after_set
        cls.sequence = sequence
        cls.think_time = think_time
        cls.verbosity = verbosity
        cls.macro_class = macro_class

        # Add all webtest filenames in all test sets
        for test_set in cls.test_sets:
            for filename in test_set.filenames:
                cls._add_webtest_file(filename)
        # If before_set was provided, add its webtest files
        if cls.before_set:
            for filename in cls.before_set.filenames:
                cls._add_webtest_file(filename)
        # If after_set was provided, add its webtest files
        if cls.after_set:
            for filename in cls.after_set.filenames:
                cls._add_webtest_file(filename)

        # For weighted sequencing, normalize the weights in all test sets,
        # so that they sum to 1.0 (100%)
        if cls.sequence == 'weighted':
            total = sum([test_set.weight for test_set in cls.test_sets])
            for test_set in cls.test_sets:
                test_set.weight = float(test_set.weight) / total

    # Make this a class method
    set_class_attributes = classmethod(set_class_attributes)


    # INSTANCE ATTRIBUTES AND METHODS
    # ----------------------------------------------

    def __init__(self, **variables):
        """Create a WebtestRunner instance, and run tests in the before_set.
        """
        # Dictionary of instance variables, indexed by name
        self.variables = variables

        # Delay reporting, to allow potential errors to be reported
        grinder.statistics.delayReports = True

        # Run tests in the before_set
        if self.before_set:
            self.run_test_set(WebtestRunner.before_set)


    def __del__(self):
        """Destructor--run tests in the after_set.
        """
        # Run tests in the after_set
        if self.after_set:
            self.run_test_set(WebtestRunner.after_set)


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
        returned as-is. If you need to use literal ``{`` or ``}`` characters in
        a string, precede them with a backslash, like ``\\{`` or ``\\}``.

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
        re_expansion = re.compile(r'((?:[^{\\]|\\.)*){((?:[^}\\]|\\.)*)}(.*)')
        # VAR_NAME=macro(args)
        re_var_macro = re.compile('([_A-Z0-0-99]+) ?= ?([_a-z]+)\(([^)]*)\)')
        # VAR_NAME=literal
        re_var_literal = re.compile('([_A-Z0-9]+) ?= ?([^}]+)')
        # macro(args)
        re_macro = re.compile('([_a-z]+)\(([^)]*)\)')
        # VAR_NAME
        re_var = re.compile('([_A-Z0-9]+)')

        macro = WebtestRunner.macro_class()

        # Match and replace until no {...} expressions are found
        to_expand = re_expansion.match(value)
        while to_expand:
            before, expression, after = to_expand.groups()

            # VAR_NAME=macro(args)
            if re_var_macro.match(expression):
                name, macro_name, args = re_var_macro.match(expression).groups()
                expanded = self.variables[name] = macro.invoke(macro_name, args)

            # VAR_NAME=literal
            elif re_var_literal.match(expression):
                name, literal = re_var_literal.match(expression).groups()
                self.variables[name] = literal
                expanded = literal

            # macro(args)
            elif re_macro.match(expression):
                macro_name, args = re_macro.match(expression).groups()
                expanded = macro.invoke(macro_name, args)

            # VAR_NAME
            elif re_var.match(expression):
                name = re_var.match(expression).groups()[0]
                if name in self.variables:
                    expanded = self.variables[name]
                else:
                    raise NameError("Variable '%s' is not initialized!" % name)

            # Invalid expression
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
        part you want to capture (leave out the parentheses to capture the
        entire match). For example, if your response contains::

            ... <a href="http://python.org"> ...

        And you want to store the URL into a variable called ``HREF``, do::

            {HREF = <a href="([^"]+)">}

        If any capture expression is not found in the response, a `CaptureFailed`
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
        body = str(response.getText())
        # Evaluate each {...} expression found in the list of request.captures()
        for expression in request.captures():
            # Error if this expression doesn't look like a capture
            match = re_capture.search(expression)
            if not match:
                message = "Syntax error in capture expression '%s'" % expression
                message += " in request defined on line %d" % request.line_number
                raise SyntaxError(message)

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
                log("!!!!!! In request defined on line %d" % request.line_number)
                log("!!!!!! Response body:")
                log(body)
                raise CaptureFailed("No match for %s" % regexp)

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
            message = "Unknown HTTP method: '%s'" % request.method
            message += " in request defined on line %d" % request.line_number
            raise ValueError(message)

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


    def run_test_set(self, test_set):
        """Run all ``.webtest`` files in the given `TestSet`.
        """
        # TODO: Reduce the amount of stuff inside this try block
        try:
            for filename in test_set.filenames:
                if WebtestRunner.verbosity != 'error':
                    log("==== Executing: %s ==========" % filename)

                # Execute all requests in this test set, in order
                for test, wrapper, request in WebtestRunner.webtest_requests[filename]:
                    # Execute this request
                    response = self.execute(test, wrapper, request)

                    # If response was not valid, report an error
                    if response.getStatusCode() >= 400:
                        grinder.statistics.forLastTest.success = False

                    # Sleep
                    grinder.sleep(WebtestRunner.think_time)

        # If problems occurred, report an error
        except CaptureFailed:
            grinder.statistics.forLastTest.success = False


    def __call__(self):
        """Execute all requests according to the class attribute ``sequence``,
        waiting ``think_time`` between each request.
        """
        # Determine which sequencing to use
        sequence = WebtestRunner.sequence
        # Run a single TestSet at random.
        if sequence == 'random':
            test_set = random.choice(WebtestRunner.test_sets)
            self.run_test_set(test_set)

        # Run a single TestSet based on the current thread number
        elif sequence == 'thread':
            index = grinder.getThreadNumber() % len(WebtestRunner.test_sets)
            test_set = WebtestRunner.test_sets[index]
            self.run_test_set(test_set)

        # Run a TestSet based on a percentage-based weight
        elif sequence == 'weighted':
            # Get a random number between 0.0 and 1.0
            pick = random.random()
            # Figure out which TestSet to run, by determining an interval
            # for each one; whichever interval pick falls into is the test
            # that will be run (assumes all TestSet weights are normalized)
            left, right = 0.0, 0.0
            for test_set in WebtestRunner.test_sets:
                left = right
                right = left + test_set.weight
                if left <= pick and pick <= right:
                    break
            # Run the TestSet that was selected
            self.run_test_set(test_set)

        # Run all TestSets sequentially
        else: # assume 'sequential'
            for test_set in WebtestRunner.test_sets:
                self.run_test_set(test_set)


def get_test_runner(test_sets,
                    before_set=None,
                    after_set=None,
                    sequence='sequential',
                    think_time=500,
                    verbosity='quiet',
                    variables={},
                    macro_class=macro.Macro):
    """Return a `TestRunner` base class that runs ``.webtest`` files in the
    given list of `TestSet`\s.

        ``variables``
            Default variables for all `TestRunner` instances. Each
            `TestRunner` instance will get their own copy of these, but
            passing them here lets you define defaults for commonly-used
            variables like server name, username, or password.

    See `WebtestRunner.set_class_attributes` for documentation on the other
    parameters.
    """
    WebtestRunner.set_class_attributes(test_sets,
        before_set, after_set, sequence, think_time, verbosity, macro_class)

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


