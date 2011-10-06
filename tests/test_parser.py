# test_parser.py

"""Unit tests for the `webtest.parser` module.
"""

import os
from . import data_dir
from webtest import parser
import unittest

class TestParser (unittest.TestCase):
    def test_well_formed(self):
        """A well-formed webtest file is correctly parsed.
        """
        # Test a valid webtest file with three requests
        webtest_file = os.path.join(data_dir, 'login.webtest')
        w = parser.Webtest(webtest_file)

        # Request info is correct
        self.assertEqual(w.filename, webtest_file)
        self.assertEqual(len(w.requests), 3)
        self.assertTrue('login.webtest' in str(w))
        self.assertTrue('Login to the application' in str(w))

        # Data in all three requests was correctly parsed
        first, second, third = w.requests
        # First request
        self.assertEqual(first.url, 'http://{SERVER}/')
        self.assertEqual(first.method, 'GET')
        self.assertEqual(first.description, 'Load the application homepage')
        self.assertEqual(first.headers, [
            (u'Content-Type', u'text/xml; charset=utf-8'),
        ])
        self.assertEqual(first.parameters, [])
        self.assertTrue(str(first).startswith("Load the application homepage"))

        # Second request
        self.assertEqual(second.url, 'http://{SERVER}/login')
        self.assertEqual(second.method, 'POST')
        self.assertEqual(second.description, 'Login to the application')
        self.assertEqual(second.headers, [
            (u'Content-Type', u'text/xml; charset=utf-8'),
        ])
        self.assertEqual(second.parameters, [
            (u'username', u'{USERNAME}'),
            (u'password', u'{PASSWORD}'),
        ])
        self.assertEqual(second.body.strip(), '')
        self.assertTrue(str(second).startswith("Login to the application"))

        # Third request
        self.assertEqual(third.url, 'http://{SERVER}/hello')
        self.assertEqual(third.method, 'POST')
        self.assertEqual(third.description, 'A post with body text')
        self.assertEqual(third.headers, [
            (u'Content-Type', u'text/xml; charset=utf-8'),
        ])
        self.assertEqual(third.parameters, [])
        self.assertEqual(third.body.strip(), u'Hello world')
        self.assertTrue(str(third).startswith("A post with body text"))


    def test_deferred_load(self):
        """Webtest can be initialized separately from loading a .webtest file.
        """
        # Empty Webtest
        w = parser.Webtest()
        self.assertEqual(w.filename, '')
        self.assertEqual(len(w.requests), 0)
        self.assertEqual(str(w), 'Empty Webtest')

        # Load a file
        webtest_file = os.path.join(data_dir, 'login.webtest')
        w.load(webtest_file)
        self.assertEqual(w.filename, webtest_file)
        self.assertEqual(len(w.requests), 3)
        self.assertTrue('login.webtest' in str(w))
        self.assertTrue('Login to the application' in str(w))


    def test_captures(self):
        """Single-capture expressions in a .webtest file are parsed correctly.
        """
        webtest_file = os.path.join(data_dir, 'captures.webtest')
        w = parser.Webtest(webtest_file)
        first, second, third, fourth = w.requests

        self.assertEqual(first.description, 'Single parenthesized')
        self.assertEqual(first.captures(), [
            u'{SID_CONTENT = <SID>([^<]+)</SID>}',
        ])

        self.assertEqual(second.description, 'Single unparenthesized')
        self.assertEqual(second.captures(), [
            u'{SID_ELEMENT = <SID>[^<]+</SID>}',
        ])

        self.assertEqual(third.description, 'Multiple parenthesized')
        self.assertEqual(third.captures(), [
            u'{SID_CONTENT = <SID>([^<]+)</SID>}',
            u'{FOO_CONTENT = <FOO>([^<]+)</FOO>}',
        ])

        self.assertEqual(fourth.description, 'Multiple unparenthesized')
        self.assertEqual(fourth.captures(), [
            u'{SID_ELEMENT = <SID>[^<]+</SID>}',
            u'{FOO_ELEMENT = <FOO>[^<]+</FOO>}',
        ])


    def test_malformed(self):
        """Test the `Webtest` class with malformed .webtest files.
        """
        # Test a malformed webtest file
        malformed_files = [
            os.path.join(data_dir, 'malformed_1.webtest'),
            os.path.join(data_dir, 'malformed_2.webtest'),
            os.path.join(data_dir, 'malformed_3.webtest'),
            os.path.join(data_dir, 'malformed_4.webtest'),
        ]
        for filename in malformed_files:
            self.assertRaises(parser.MalformedXML, parser.Webtest, filename)

