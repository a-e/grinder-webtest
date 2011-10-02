# test_macro.py

"""Unit tests for the `webtest.macro` module.
"""

import re
from webtest.macro import Macro
import unittest

class MacroTest (unittest.TestCase):
    def test_invoke_macro(self):
        """Test the Macro ``invoke`` method.
        """
        M = Macro()

        # Random digits
        digits = M.invoke('random_digits', '5')
        self.assertTrue(re.match('^\d{5}$', digits))

        # Random letters
        letters = M.invoke('random_letters', '5')
        self.assertTrue(re.match('^[A-Z]{5}$', letters))

        # Random alphanumeric
        alpha = M.invoke('random_alphanumeric', '5')
        self.assertTrue(re.match('^[A-Z0-9]{5}$', alpha))

        # Today
        today = M.invoke('today', '%Y/%m/%d')
        self.assertTrue(re.match('^\d{4}/\d{2}/\d{2}$', today))

        # Tomorrow
        tomorrow = M.invoke('today_plus', '1, %Y/%m/%d')
        self.assertTrue(re.match('^\d{4}/\d{2}/\d{2}$', tomorrow))

        # Unknown macro
        self.assertRaises(ValueError, M.invoke, 'bogus', '0')

