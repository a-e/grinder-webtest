# __init__.py

"""Setup and teardown methods for Grinder Webtest unit tests.
"""

import os
import sys

# Directory where test data files are stored
data_dir = os.path.join(os.path.dirname(__file__), 'data')

# Package-level setup and teardown

def setup():
    """Package-level setup.
    """
    # Append to sys.path in case csvsee isn't installed
    sys.path.append(os.path.abspath('..'))


def teardown():
    """Package-level teardown.
    """
    pass

