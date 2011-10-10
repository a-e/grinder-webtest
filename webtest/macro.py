# macro.py

"""This module defines macro functions that can be invoked from a webtest.
Macros provide a way of programmatically generating things like timestamps,
random strings or numbers, or other strings that cannot be hard-coded.

Macro functions are defined as methods within the `Macro` class. Any methods
defined in this module are built-in, so you can invoke them from any evaluated
expression in a ``.webtest`` file.

All macro functions are invoked using a ``lower_case`` name followed by
parentheses. If the macro accepts arguments, they are passed as a literal
string, separated by commas. For example::

    <FormPostParameter Name="TIMESTAMP" Value="{timestamp()}"/>
    <FormPostParameter Name="INVOICE_DATE" Value="{today(%y%m%d)}"/>
    <FormPostParameter Name="DUE_DATE" Value="{today_plus(7, %y%m%d)}"/>

You can also assign the return value of a macro to a variable, for later use::

    <FormPostParameter Name="TIMESTAMP" Value="{NOW = timestamp()}"/>
    <FormPostParameter Name="INVOICE_DATE" Value="{TODAY = today(%y%m%d)}"/>
    <FormPostParameter Name="DUE_DATE" Value="{NEXT_WEEK= today_plus(7, %y%m%d)}"/>

If you want to define your own custom macros, create a derived class containing
your custom methods::

    from webtest.macro import Macro

    class MyMacro (Macro):
        # Zero-argument macro
        def pi(self):
            return '3.14159'

        # One-argument macro
        def square(self, num):
            return int(num) ** 2

        # Two-argument macro
        def multiply(self, x, y):
            return int(x) * int(y)

Then, tell your test runner to use your macro class::

    TestRunner = get_test_runner( ... , macro_class=MyMacro)

Any ``.webtest`` files that are executed by this TestRunner will be able to call
your custom macro methods, optionally storing their results in variables::

    <FormPostParameter Name="NUM1" Value="{PI = pi()}" />
    <FormPostParameter Name="NUM2" Value="{square(5)}" />
    <FormPostParameter Name="NUM3" Value="{PRODUCT = multiply(3, 6)}" />

All macro arguments are strings; if your arguments are intended to be numeric,
you must convert them yourself. The return value will also be converted to
a string; it's converted automatically when your macro is invoked, but you
may want to convert it yourself to ensure you get exactly what you want.
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
    """
    def __init__(self):
        pass

    def invoke(self, macro_name, args):
        """Invoke ``macro_name``, passing ``args``, and return the result.
        This is a helper method and should not be called as a macro.
        """
        # Don't allow calling invoke itself as a macro
        if macro_name == 'invoke':
            raise ValueError("Cannot call 'invoke' as a macro")

        # Unpack the arguments
        unpacked = [arg.strip() for arg in args.split(',')]
        # [''] is equivalent to 0 arguments
        if unpacked == ['']:
            unpacked = []

        try:
            func = getattr(self, macro_name)
        except AttributeError:
            raise ValueError("Macro function '%s' is undefined" % macro_name)
        else:
            return str(func(*unpacked))

    def random_digits(self, length):
        """Generate a random string of digits of the given length.
        For example, ``random_digits(5)`` might return ``28571``.
        """
        return ''.join(_sample('0123456789', int(length)))

    def random_letters(self, length):
        """Generate a random string of letters of the given length.
        For example, ``random_letters(5)`` might return ``KPDLE``.
        """
        return ''.join(_sample('ABCDEFGHIJKLMNOPQRSTUVWXYZ', int(length)))

    def random_alphanumeric(self, length):
        """Generate a random alphanumeric string of the given length.
        For example, ``random_alphanumeric(5)`` might return ``F31B9``.
        """
        return ''.join(_sample('0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ', int(length)))

    def now(self, format='%Y-%m-%d %H:%M:%S'):
        """Return the current date/time in the given format. For example,
        ``%m%d%y`` for ``MMDDYY`` format. See the datetime_ module
        documentation for allowed format strings. For example,
        ``today(%y-%m-%d)`` might return ``2011-10-06``.

        .. _datetime: http://docs.python.org/library/datetime.html
        """
        return datetime.datetime.now().strftime(format)
    today = now

    def today_plus(self, days, format='%Y-%m-%d'):
        """Return today plus some number of days, in the given format.
        For example, ``today_plus(9, %Y-%m-%d)`` might return ``2011-10-15``.
        """
        return (datetime.datetime.now() + datetime.timedelta(int(days))).strftime(format)

    def timestamp(self):
        """Return a timestamp (number of seconds since the epoch). For example,
        ``timestamp()`` might return ``1317917454``.
        """
        return str(int(time.time()))


