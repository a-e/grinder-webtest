# macro.py

"""Macro functions that can be invoked from a webtest.
"""

import random
import datetime
import time

def _sample(choices, how_many):
    """Return `how_many` randomly-chosen items from `choices`.
    """
    return [random.choice(choices) for x in range(how_many)]

class Macro:
    """Functions that can be invoked from a webtest.

    Macro functions each accept a string argument, and return a string.
    If a macro needs to accept several arguments, they should be packed
    into a string and separated with commas.
    """
    def __init__(self):
        pass

    def invoke(self, macro_name, args):
        """Invoke ``macro_name``, passing ``args``, and return the result.
        """
        try:
            func = getattr(self, macro_name)
        except AttributeError:
            raise ValueError("Macro function '%s' is undefined")
        else:
            return str(func(args))

    def random_digits(self, length):
        """Generate a random string of digits of the given length.
        """
        return ''.join(_sample('0123456789', int(length)))

    def random_letters(self, length):
        """Generate a random string of letters of the given length.
        """
        return ''.join(_sample('ABCDEFGHIJKLMNOPQRSTUVWXYZ', int(length)))

    def random_alphanumeric(self, length):
        """Generate a random alphanumeric string of the given length.
        """
        return ''.join(_sample('0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ', int(length)))

    def today(self, format):
        """Return today's date in the given format. For example, ``%m%d%y`` for
        ``MMDDYY`` format. See the datetime_ module documentation for allowed
        format strings.

        .. _datetime: http://docs.python.org/library/datetime.html
        """
        return datetime.date.today().strftime(format)

    def today_plus(self, days_and_format):
        """Return today plus some number of days, in the given format.
        """
        days, format = [arg.strip() for arg in days_and_format.split(',')]
        return (datetime.date.today() + datetime.timedelta(int(days))).strftime(format)

    def timestamp(self, arg):
        """Return a timestamp (number of seconds since the epoch).
        """
        return str(int(time.time()))


