# test_parser.py

"""Unit tests for the `webtest.parser` module.
"""

import os
from nose.tools import assert_raises
from . import data_dir
from webtest import parser

def test_well_formed():
    """Test the `Webtest` class with a well-formed .webtest file.
    """
    # Test a valid webtest file with a single request
    login_file = os.path.join(data_dir, 'login.webtest')
    w = parser.Webtest(login_file)

    # Ensure the Webtest fields match expectations
    assert w.filename == login_file
    assert len(w.requests) == 1
    assert 'login.webtest' in str(w)
    assert 'Login to the application' in str(w)

    # Ensure the request matches expectations
    req = w.requests[0]
    assert req.url == 'http://{SERVER}/login'
    assert req.method == 'GET'
    assert req.description == 'Login to the application'
    assert req.headers == [
        (u'Content-Type', u'text/xml; charset=utf-8'),
    ]
    assert req.parameters == [
        (u'username', u'{USERNAME}'),
        (u'password', u'{PASSWORD}'),
    ]
    assert req.captures() == [
        u'{SESSION_ID = <SID>([^<]+)</SID>}',
    ]
    assert str(req).startswith("Login to the application")


def test_malformed():
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
        assert_raises(parser.MalformedXML, parser.Webtest, filename)

