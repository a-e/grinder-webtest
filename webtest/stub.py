# stub.py

"""Stub objects to use for testing when Grinder libraries are not available.
"""

class Stub (object):
    """A fake class used for stubs/mocks.
    """
    def __init__(self, *args, **kw):
        pass

    def __getattribute__(self, name):
        return Stub()

    def __setattribute__(self, name, value):
        pass

    def __call__(self, *args, **kw):
        return Stub()

    def __str__(self):
        return 'Stub'

grinder = Stub()
log = Stub()
NVPair = Stub()
HTTPRequest = Stub()

class Test:
    def __init__(self, number, description):
        self.number = number
        self.description = description

    def getNumber(self):
        return self.number

    def wrap(self, *args):
        return Stub()

class Response:
    def __init__(self, body=''):
        self.body = body

    def getText(self):
        return self.body

