# parser.py

"""Provides classes for parsing Visual Studio ``.webtest`` XML files.

The Visual Studio ``.webtest`` XML format does not seem to be documented
anywhere, so all the elements and attributes used here are inferred from the
``.webtest`` files written by Fiddler_.

.. _Fiddler: http://www.fiddler2.com/fiddler2/

This module defines three important classes:

    `Webtest`
        Parses a ``.webtest`` file and gets a list of `Request` objects
    `Request`
        Stores attributes and contents relevant to a single HTTP(S) request
    `WebtestHandler`
        Used internally by the sax XML parser

The `Webtest` class is the one you're most likely to use directly. Simply
provide the name of a ``.webtest`` XML file::

    >>> my_test = Webtest('my_test.webtest')

If you provide a filename to the constructor, parsing is done automatically.
Alternatively, you can delay parsing until later::

    >>> my_test = Webtest()
    ...
    >>> my_test.parse('my_test.webtest')

After parsing, the `Webtest` object will contain a list of `Request` objects.
You can print all requests in summarized form::

    >>> print(my_test)

Or iterate over the requests and do something with them::

    >>> for request in my_test.requests:
    ...     do_something(request)

The ``.webtest`` file is expected to have one or more ``Request`` elements,
similar to the one below::

    <Request Method="POST" Url="http://www.example.com/">
      <Headers>
        <Header Name="Content-Type" Value="text/plain" />
      </Headers>
      <FormPostHttpBody ContentType="text/plain">
        <FormPostParameter Name="username" Value="phil" />
        <FormPostParameter Name="session_id" Value="12345" />
      </FormPostHttpBody>
    </Request>

Each ``<Request>...</Request>`` defines a single HTTP request to a particular
URL, using a method of GET or POST. Headers are enclosed in a ``<Header .../>``
element, and any parameters are sent using ``<FormPostParameter .../>``, both
of which have ``Name`` and ``Value`` attributes.

Two additional elements are understood by this parser:

    ``<Description>...</Description>``
        A human-readable string that describes what the request does
    ``<Capture>...</Capture>``
        A block of expressions that may be used to capture or verify
        content in the body of the response for this request

This module is designed to be used with the `webtest.runner` module, which is
specifically designed to work with the Grinder load test framework, but the
parser defined here is not Grinder-specific, and can be used for more
general-purpose parsing of ``.webtest`` files.
"""

# Everything in this script should be compatible with Jython 2.2.1.

import sys
from xml import sax
from urlparse import urlparse


class MalformedXML (Exception):
    """Raised when any malformed XML is encountered."""
    pass


class Request:
    """Store attributes pertaining to an HTTP Request, including:

        url
            The full URL path of the request
        headers
            A list of ``(Name, Value)`` for the request header
        parameters
            A list of ``(Name, Value)`` for the request parameters

    """
    def __init__(self, attrs, line_number=0):
        """Create a Request with the given attributes.
        """
        self.url = attrs.get('Url', '')
        self.method = attrs.get('Method', 'GET')
        # Keep track of body, headers and parameters for this request
        self.body = ''
        self.headers = []
        self.parameters = []
        # List of expressions to capture response data
        self.capture = ''
        # Human-readable description of the request
        self.description = ''
        # Line number where this request was defined
        self.line_number = line_number


    def _add_attrs(self, attrs, to_list):
        """Add a ``(Name, Value)`` pair to a given list.

        attrs
            A `dict` including 'Name' and 'Value' items
        to_list
            The list to append ``(Name, Value)`` to

        If the 'Name' or 'Value' attributes are not defined, or if the 'Name'
        attribute is empty, nothing is added.
        """
        # Only add if attrs has a non-empty 'Name',
        # and 'Value' is defined (possibly empty)
        if attrs.get('Name') and 'Value' in attrs:
            name = attrs['Name']
            value = attrs['Value']
            # Create and append the pair
            pair = (name, value)
            to_list.append(pair)


    def add_header(self, attrs):
        """Add a header ``(Name, Value)`` pair to the request.

        attrs
            A `dict` including 'Name' and 'Value' items

        If the 'Name' or 'Value' attributes are not defined, or if the 'Name'
        attribute is empty, nothing is added.
        """
        self._add_attrs(attrs, self.headers)


    def add_parameter(self, attrs):
        """Add a parameter ``(Name, Value)`` pair to the request.

        attrs
            A `dict` including 'Name' and 'Value' items

        If the 'Name' or 'Value' attributes are not defined, or if the 'Name'
        attribute is empty, nothing is added.
        """
        self._add_attrs(attrs, self.parameters)


    def captures(self):
        """Return capture expressions as a list of strings.

        Normally, ``self.capture`` will be a literal block of text as it
        appeared inside the ``Capture`` element; it may contain extra spaces
        and newlines.  This method strips out the extra newlines and
        whitespace, and converts to a list for easy iteration over each capture
        expression.
        """
        result = []
        for line in self.capture.splitlines():
            if line.strip() != '':
                result.append(line.strip())
        return result


    def __str__(self):
        """Return a one-line string summarizing the request.
        """
        result = ''
        # Include the request description first
        if self.description:
            result = self.description + ': '
        # Append the URL and its parameters
        # Start with method
        result += self.method
        # Add the URL (minus the http:// part)
        server, path = urlparse(self.url)[1:3]
        result += ' ' + server + path
        # Add parameters, formatted like a dict
        result += ' {%s}' % ', '.join(
            ["'%s': '%s'" % pair for pair in self.parameters])
        return result


class WebtestHandler (sax.handler.ContentHandler):
    """Content handler for xml.sax parser.
    """
    def __init__(self):
        """Create the Webtest content handler.
        """
        sax.handler.ContentHandler.__init__(self)
        self.request = None
        self.requests = []
        # String to indicate when we're inside particular elements
        self.in_element = ''
        # Locator used to track line numbers
        self.locator = None


    def setDocumentLocator(self, locator):
        """Set the document locator, for tracking line numbers.
        This is set by the parser, and is used in `startElement`.
        """
        self.locator = locator


    def startElement(self, name, attrs):
        """Called when an opening XML tag is found. If any badly-formed
        XML is encountered, a `MalformedXML` exception is raised.
        """
        # With sax, attrs is almost, but not quite, a dictionary.
        # Convert it here to make things easier in the Request class.
        attrs = dict(attrs.items())

        # Determine which element is being started, and take
        # appropriate action

        # Request element? Create a new Request object
        if name == 'Request':
            self.request = Request(attrs, self.locator.getLineNumber())

        # Header element? Add the header to the current request
        elif name == 'Header':
            if not self.request:
                raise MalformedXML("%s not inside Request" % name)
            self.request.add_header(attrs)

        # Parameter element? Add the parameter to the current request
        elif name in ('QueryStringParameter', 'FormPostParameter'):
            if not self.request:
                raise MalformedXML("%s not inside Request" % name)
            self.request.add_parameter(attrs)

        # The 'StringHttpBody', 'Capture', and 'Description' elements do not
        # have any attributes, only content. Make note of when we enter them,
        # so the characters() method can fetch their content.
        elif name in ('StringHttpBody', 'Capture', 'Description'):
            self.in_element = name

        # We don't care about any other elements
        else:
            pass


    def characters(self, data):
        """Called when character data is found inside an element.
        """
        # Ignore any empty data, or characters outside a known element
        if not (data and self.in_element):
            return

        # If we're not inside a request, something is wrong
        if not self.request:
            raise MalformedXML("Characters in %s not inside Request" % \
                               self.in_element)

        # Otherwise, save the data to the appropriate place.
        # Append, since characters() may be called with arbitrarily
        # small chunks of text, and we don't want to miss anything.
        if self.in_element == 'StringHttpBody':
            self.request.body += data
        elif self.in_element == 'Capture':
            self.request.capture += data
        elif self.in_element == 'Description':
            self.request.description += data


    def endElement(self, name):
        """Called when a closing XML tag is found.
        """
        # If this is the end of the Request,
        # append to requests and clear current request
        if name == 'Request':
            self.requests.append(self.request)
            self.request = None

        # For elements with character content, reset in_element
        elif name in ('StringHttpBody', 'Capture', 'Description'):
            self.in_element = ''

        # No action needed for closing other elements
        else:
            pass


class Webtest:
    """Webtest XML file parser.
    """
    def __init__(self, filename=''):
        """Get requests from the given ``.webtest`` XML file.
        After calling this, the ``requests`` attribute will have a
        list of all requests found in the given ``.webtest`` file.
        """
        self.filename = filename
        self.requests = []
        # Create the handler and sax parser
        self._handler = WebtestHandler()
        self.saxparser = sax.make_parser()
        self.saxparser.setContentHandler(self._handler)
        # Parse the file, if given
        if filename:
            self.parse(filename)


    def parse(self, filename):
        """Parse the given ``.webtest`` XML file, and store the
        list of requests found in it.
        """
        self.filename = filename
        # Parse the given filename
        infile = open(filename, 'r')
        try:
            self.saxparser.parse(infile)
        except sax.SAXParseException, e:
            raise MalformedXML(e)
        infile.close()
        # Store a reference to the list of requests
        self.requests = self._handler.requests


    def __str__(self):
        """Return the Webtest formatted as a human-readable string.
        """
        result = 'Webtest: %s\n\n' % self.filename
        result += '\n\n'.join([str(req) for req in self.requests])
        return result


