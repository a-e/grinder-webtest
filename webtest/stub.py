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

def log(message):
    print(message)

class Wrapper:
    def __init__(self):
        pass

    def GET(self, *args):
        return Response()

    def POST(self, *args):
        return Response()

class Test:
    def __init__(self, number, description):
        self.number = number
        self.description = description

    def getNumber(self):
        return self.number

    def wrap(self, *args):
        return Wrapper()

class Response:
    def __init__(self, body=''):
        self.body = body

    def getText(self):
        return self.body

    def getStatusCode(self):
        return 200

class StatisticsForTest:
    def __init__(self):
        self.success = True

class Statistics:
    def __init__(self):
        self.forLastTest = StatisticsForTest()
        self.delayReports = False

class Grinder:
    __shared_state = {}
    def __init__(self):
        self.__dict__ = self.__shared_state
        self.statistics = Statistics()

    def sleep(self, *args):
        pass

    def getThreadNumber(self, *args):
        return 0

grinder = Grinder()
NVPair = Stub()
HTTPRequest = Stub()

