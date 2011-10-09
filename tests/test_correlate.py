# test_runner.py

"""Unit tests for the `webtest.runner` module.
"""

import os
import unittest
from . import data_dir
from webtest import correlate
from webtest import runner

class TestCorrelationRunner (unittest.TestCase):
    def test_get_correlation_runner(self):
        login_file = os.path.join(data_dir, 'login.webtest')
        login_test = runner.TestSet(login_file)
        corr_runner = correlate.get_correlation_runner(
            [login_test],
        )
        self.assertEqual(type(corr_runner), type(correlate.CorrelationRunner))

