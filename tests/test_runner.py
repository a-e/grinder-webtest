# test_runner.py

"""Unit tests for the `webtest.runner` module.
"""

import os
import re
from . import data_dir
from nose.tools import assert_raises
from webtest import runner

def test_macro():
    """Test the `macro` function.
    """
    # Random digits
    digits = runner.macro('random_digits', 5)
    assert re.match('^\d{5}$', digits)
    # Random letters
    letters = runner.macro('random_letters', 5)
    assert re.match('^[A-Z]{5}$', letters)
    # Random alphanumeric
    alpha = runner.macro('random_alphanumeric', 5)
    assert re.match('^[A-Z0-9]{5}$', alpha)
    # Today
    today = runner.macro('today', '%Y/%m/%d')
    assert re.match('^\d{4}/\d{2}/\d{2}$', today)
    # Tomorrow
    tomorrow = runner.macro('today_plus', '1, %Y/%m/%d')
    assert re.match('^\d{4}/\d{2}/\d{2}$', tomorrow)
    # Unknown macro
    assert_raises(NameError, runner.macro, 'no_such_macro')


def test_TestSet():
    """Test the `TestSet` class.
    """
    login_file = os.path.join(data_dir, 'login.webtest')
    ts = runner.TestSet(login_file)
    assert len(ts.filenames) == 1
    assert ts.filenames == [login_file]
    assert ts.weight == 1.0


def test_get_test_runner():
    """Test the `get_test_runner` function.
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
    assert type(test_runner) == type(runner.WebtestRunner)
    assert len(test_runner.test_sets) == 1


def test_get_test_runner_exceptions():
    """Test exceptional conditions from the `get_test_runner` function.
    """
    login_file = os.path.join(data_dir, 'login.webtest')
    test_sets = [
        runner.TestSet(login_file),
    ]
    GTR = runner.get_test_runner
    # test_sets that isn't a list
    assert_raises(ValueError, GTR, 'foo')
    # test_sets items aren't TestSet objects
    assert_raises(ValueError, GTR, ['foo'])
    # Invalid sequence keyword
    assert_raises(ValueError, GTR, test_sets, sequence='blah')
    # Invalid verbosity keyword
    assert_raises(ValueError, GTR, test_sets, verbosity='blah')
    # Invalid before_set
    assert_raises(ValueError, GTR, test_sets, before_set='blah')
    # Invalid after_set
    assert_raises(ValueError, GTR, test_sets, after_set='blah')


def test_running():
    """Test mock-running of tests.
    """
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

