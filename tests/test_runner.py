# test_runner.py

"""Unit tests for the `webtest.runner` module.
"""

import os
import re
import unittest
from . import data_dir
from webtest import runner
from webtest import parser
from webtest import stub

class TestSetTest (unittest.TestCase):
    def test_TestSet(self):
        """Test the `TestSet` class.
        """
        login_file = os.path.join(data_dir, 'login.webtest')
        ts = runner.TestSet(login_file)
        self.assertEqual(len(ts.filenames), 1)
        self.assertEqual(ts.filenames, [login_file])
        self.assertEqual(ts.weight, 1.0)


class TestWebtestRunner (unittest.TestCase):
    def test_get_test_runner(self):
        """get_test_runner returns a WebtestRunner class.
        """
        login_file = os.path.join(data_dir, 'login.webtest')
        login_test = runner.TestSet(login_file)
        # Quick-and-dirty--just use the login test for test_sets,
        # before_set and after_set
        test_runner = runner.get_test_runner(
            [login_test],
            before_set=login_test,
            after_set=login_test,
            verbosity='debug',
            sequence='weighted')
        self.assertEqual(type(test_runner), type(runner.WebtestRunner))
        self.assertEqual(len(test_runner.test_sets), 1)


    def test_get_test_runner_exceptions(self):
        """get_test_runner raises exceptions for bad arguments.
        """
        login_file = os.path.join(data_dir, 'login.webtest')
        test_sets = [
            runner.TestSet(login_file),
        ]
        GTR = runner.get_test_runner
        # test_sets that isn't a list
        self.assertRaises(ValueError, GTR, 'foo')
        # test_sets items aren't TestSet objects
        self.assertRaises(ValueError, GTR, ['foo'])
        # Invalid sequence keyword
        self.assertRaises(ValueError, GTR, test_sets, sequence='blah')
        # Invalid verbosity keyword
        self.assertRaises(ValueError, GTR, test_sets, verbosity='blah')
        # Invalid before_set
        self.assertRaises(ValueError, GTR, test_sets, before_set='blah')
        # Invalid after_set
        self.assertRaises(ValueError, GTR, test_sets, after_set='blah')
        # Invalid macro_class
        self.assertRaises(ValueError, GTR, test_sets, macro_class='blah')


    def test_running(self):
        """WebtestRunner can run tests.
        """
        login_file = os.path.join(data_dir, 'login.webtest')
        login_test = runner.TestSet(login_file)
        my_vars = {
            'SERVER': 'www.google.com',
            'USERNAME': 'wapcaplet',
            'PASSWORD': 'f00b4r',
        }
        # Get the test runner
        test_runner = runner.get_test_runner(
            [login_test], verbosity='debug', variables=my_vars)

        # Instantiate the test runner
        runner_instance = test_runner()

        # Call the runner to execute tests
        result = runner_instance()
        self.assertEqual(result, True)

        # TODO: Test random, thread, weighted


    def test_bad_request_method(self):
        """WebtestRunner raises exception on bad request method.
        """
        login_file = os.path.join(data_dir, 'bad_method.webtest')
        login_test = runner.TestSet(login_file)

        # Get the test runner
        test_runner = runner.get_test_runner([login_test], verbosity='debug')

        # Instantiate the test runner
        runner_instance = test_runner()

        # Calling the runner should raise an exception for
        # the bad request method
        self.assertRaises(ValueError, runner_instance)


    def test_eval_expressions(self):
        """WebtestRunner correctly evaluates expressions.
        """
        my_vars = {
            'SERVER': 'www.google.com',
            'USERNAME': 'wapcaplet',
            'PASSWORD': 'f00b4r',
        }
        # Get a dummy test runner instance
        tr = runner.get_test_runner([], variables=my_vars)()
        # Shortcut to eval
        ee = tr.eval_expressions

        # Simple variable expansion
        self.assertEqual(ee('{SERVER}'), 'www.google.com')
        self.assertEqual(ee('{USERNAME}'), 'wapcaplet')
        self.assertEqual(ee('{PASSWORD}'), 'f00b4r')

        # Variable expansion with surrounding text
        self.assertEqual(ee('http://{SERVER}/'), 'http://www.google.com/')
        self.assertEqual(ee('User="{USERNAME}"'), 'User="wapcaplet"')
        self.assertEqual(ee('Pass="{PASSWORD}"'), 'Pass="f00b4r"')

        # Multiple-variable expansion
        self.assertEqual(ee('User:{USERNAME};Pass:{PASSWORD}'), 'User:wapcaplet;Pass:f00b4r')

        # Variable assignment
        expanded = ee('Userid: {UID = 1234}')
        self.assertEqual(expanded, 'Userid: 1234')
        self.assertEqual(ee('Userid: {UID}'), 'Userid: 1234')

        # Macro evaluation
        expanded = ee('Random: {random_digits(5)}')
        self.assertTrue(re.match('^Random: \d{5}$', expanded))

        # Macro evaluation and assignment
        expanded = ee('Random: {DIGITS = random_digits(5)}')
        match = re.match('^Random: (\d{5})$', expanded)
        self.assertTrue(match) # Got a 5-digit number
        # DIGITS alone expands to the previously-expanded value
        self.assertEqual(ee('{DIGITS}'), match.groups()[0])

        # Escaped braces
        self.assertEqual(ee('Literal \{braces\}'),
                            'Literal \{braces\}')
        self.assertEqual(ee('Literal \{braces with {USERNAME} inside\}'),
                            'Literal \{braces with wapcaplet inside\}')

        # Exception when variable is not initialized
        self.assertRaises(NameError, ee, '{BOGUS}')
        # Exceptions for syntax errors
        self.assertRaises(SyntaxError, ee, '{server}')
        self.assertRaises(SyntaxError, ee, '{{SERVER}}')
        self.assertRaises(SyntaxError, ee, '{ SERVER }')

        # TODO: Macro eval, macro assignment, custom macro


class TestWebtestRunnerEvalCapture (unittest.TestCase):
    def setUp(self):
        # Dummy response to test capture evaluation
        self.response = stub.Response(
            """<?xml version="1.0" encoding="utf-8"?>
            <SessionData>
            <SID>314159265</SID>
            <FOO>112233</FOO>
            </SessionData>
            """
        )

    def test_eval_capture_single_parenthesized(self):
        """eval_capture works with a single parenthesized capture expression.
        """
        webtest_file = os.path.join(data_dir, 'captures.webtest')
        webtest_test = runner.TestSet(webtest_file)

        tr = runner.get_test_runner([webtest_test], verbosity='debug')()
        req = parser.Webtest(webtest_file).requests[0]

        captured = tr.eval_capture(req, self.response)
        self.assertEqual(captured, 1)
        self.assertEqual(tr.variables, {'SID_CONTENT': '314159265'})


    def test_eval_capture_single_unparenthesized(self):
        """eval_capture works with a single unparenthesized capture expression.
        """
        webtest_file = os.path.join(data_dir, 'captures.webtest')
        webtest_test = runner.TestSet(webtest_file)

        tr = runner.get_test_runner([webtest_test], verbosity='debug')()
        req = parser.Webtest(webtest_file).requests[1]

        captured = tr.eval_capture(req, self.response)
        self.assertEqual(captured, 1)
        self.assertEqual(tr.variables, {'SID_ELEMENT': '<SID>314159265</SID>'})


    def test_eval_capture_multiple_parenthesized(self):
        """eval_capture works with multiple parenthesized capture expressions.
        """
        webtest_file = os.path.join(data_dir, 'captures.webtest')
        webtest_test = runner.TestSet(webtest_file)

        tr = runner.get_test_runner([webtest_test], verbosity='debug')()
        req = parser.Webtest(webtest_file).requests[2]

        captured = tr.eval_capture(req, self.response)
        self.assertEqual(captured, 2)
        self.assertEqual(tr.variables, {
            'SID_CONTENT': '314159265', 'FOO_CONTENT': '112233'})


    def test_eval_capture_multiple_unparenthesized(self):
        """eval_capture works with multiple unparenthesized capture expressions.
        """
        webtest_file = os.path.join(data_dir, 'captures.webtest')
        webtest_test = runner.TestSet(webtest_file)

        tr = runner.get_test_runner([webtest_test], verbosity='debug')()
        req = parser.Webtest(webtest_file).requests[3]

        captured = tr.eval_capture(req, self.response)
        self.assertEqual(captured, 2)
        self.assertEqual(tr.variables, {
            'SID_ELEMENT': '<SID>314159265</SID>', 'FOO_ELEMENT': '<FOO>112233</FOO>'})


    def test_eval_capture_empty(self):
        """eval_capture does nothing when there are no capture expressions.
        """
        webtest_file = os.path.join(data_dir, 'login.webtest')
        webtest_test = runner.TestSet(webtest_file)

        # Get the test runner instance
        tr = runner.get_test_runner([webtest_test], verbosity='debug')()

        # Get the login POST request from captures.webtest
        request = parser.Webtest(webtest_file).requests[0]

        # Construct a dummy response
        response = stub.Response(
            """<?xml version="1.0" encoding="utf-8"?>
            <SessionData><SID>314159265</SID></SessionData>
            """)
        captured = tr.eval_capture(request, response)
        self.assertEqual(captured, 0)
        self.assertEqual(tr.variables, {})


    def test_eval_capture_syntax_error(self):
        """eval_capture raises an exception on malformed capture expressions.
        """
        webtest_file = os.path.join(data_dir, 'malformed_capture.webtest')
        webtest_test = runner.TestSet(webtest_file)

        # Get the test runner instance
        tr = runner.get_test_runner([webtest_test], verbosity='debug')()

        # Get the first request from captures.webtest
        request = parser.Webtest(webtest_file).requests[0]

        # Construct a dummy response
        response = stub.Response(
            """<?xml version="1.0" encoding="utf-8"?>
            <SessionData><SID>314159265</SID></SessionData>
            """)
        # eval_capture raises an exception
        self.assertRaises(SyntaxError, tr.eval_capture, request, response)


    def test_eval_capture_not_found(self):
        """eval_capture raises an exception when a capture expression is not matched
        """
        webtest_file = os.path.join(data_dir, 'captures.webtest')
        webtest_test = runner.TestSet(webtest_file)

        # Get the test runner instance
        tr = runner.get_test_runner([webtest_test], verbosity='debug')()

        # Get the first request from captures.webtest
        request = parser.Webtest(webtest_file).requests[1]

        # Construct a dummy response
        response = stub.Response(
            """<?xml version="1.0" encoding="utf-8"?>
            <SessionData><NOT_SID>314159265</NOT_SID></SessionData>
            """)
        # eval_capture raises an exception
        self.assertRaises(runner.CaptureFailed, tr.eval_capture, request, response)


