# test_runner.py

"""Unit tests for the `webtest.runner` module.
"""

import os
from . import data_dir
from webtest import runner
import unittest

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
        # FIXME: Need some test assertions in here!
        login_file = os.path.join(data_dir, 'login.webtest')
        login_test = runner.TestSet(login_file)
        my_vars = {
            'SERVER': 'www.google.com',
            'USERNAME': 'wapcaplet',
            'PASSWORD': 'f00b4r',
        }
        # Get the test runner
        test_runner = runner.get_test_runner([login_test], variables=my_vars)

        # Instantiate the test runner
        runner_instance = test_runner()

        # Call the runner to execute tests
        runner_instance()


    def test_eval_expressions(self):
        """WebtestRunner correctly evaluates expressions.
        """
        my_vars = {
            'SERVER': 'www.google.com',
            'USERNAME': 'wapcaplet',
            'PASSWORD': 'f00b4r',
        }
        # Get a dummy test runner instance
        TR = runner.get_test_runner([], variables=my_vars)()
        # Shortcut to eval
        ev = TR.eval_expressions

        # Simple variable expansion
        self.assertEqual(ev('{SERVER}'), 'www.google.com')
        self.assertEqual(ev('{USERNAME}'), 'wapcaplet')
        self.assertEqual(ev('{PASSWORD}'), 'f00b4r')

        # Variable expansion with surrounding text
        self.assertEqual(ev('http://{SERVER}/'), 'http://www.google.com/')
        self.assertEqual(ev('User="{USERNAME}"'), 'User="wapcaplet"')
        self.assertEqual(ev('Pass="{PASSWORD}"'), 'Pass="f00b4r"')

        # Multiple-variable expansion
        self.assertEqual(ev('User:{USERNAME};Pass:{PASSWORD}'), 'User:wapcaplet;Pass:f00b4r')

        # Variable assignment
        expanded = ev('Userid: {UID = 1234}')
        self.assertEqual(expanded, 'Userid: 1234')
        self.assertEqual(ev('Userid: {UID}'), 'Userid: 1234')

        # TODO: Macro eval, macro assignment, custom macro, escaped braces

        # Exception when variable is not initialized
        self.assertRaises(NameError, ev, '{BOGUS}')
        # Exception for bad expression
        self.assertRaises(SyntaxError, ev, '{lowercase_var}')

