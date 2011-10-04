# test_parser.py

"""Unit tests for the `webtest.parser` module.
"""

import os
from . import data_dir
from webtest import parser
import unittest

class TestParser (unittest.TestCase):
    def test_well_formed(self):
        """Test the `Webtest` class with a well-formed .webtest file.
        """
        # Test a valid webtest file with three requests
        webtest_file = os.path.join(data_dir, 'captures.webtest')
        w = parser.Webtest(webtest_file)

        # Request info is correct
        self.assertEqual(w.filename, webtest_file)
        self.assertEqual(len(w.requests), 3)
        self.assertTrue('captures.webtest' in str(w))
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
        self.assertEqual(first.captures(), [])
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
        self.assertEqual(second.captures(), [
            u'{SESSION_ID = <SID>([^<]+)</SID>}',
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
        self.assertEqual(third.captures(), [])
        self.assertEqual(third.body.strip(), u'Hello world')
        self.assertTrue(str(third).startswith("A post with body text"))


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

