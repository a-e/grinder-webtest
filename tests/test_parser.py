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
        # Test a valid webtest file with a single request
        login_file = os.path.join(data_dir, 'login.webtest')
        w = parser.Webtest(login_file)

        # Ensure the Webtest fields match expectations
        self.assertEqual(w.filename, login_file)
        self.assertEqual(len(w.requests), 1)
        self.assertTrue('login.webtest' in str(w))
        self.assertTrue('Login to the application' in str(w))

        # Ensure the request matches expectations
        req = w.requests[0]
        self.assertEqual(req.url, 'http://{SERVER}/login')
        self.assertEqual(req.method, 'GET')
        self.assertEqual(req.description, 'Login to the application')
        self.assertEqual(req.headers, [
            (u'Content-Type', u'text/xml; charset=utf-8'),
        ])
        self.assertEqual(req.parameters, [
            (u'username', u'{USERNAME}'),
            (u'password', u'{PASSWORD}'),
        ])
        self.assertEqual(req.captures(), [
            u'{SESSION_ID = <SID>([^<]+)</SID>}',
        ])
        self.assertTrue(str(req).startswith("Login to the application"))


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

