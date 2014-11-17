"""
Classes and utilities for adding location information to syntax tree nodes.
"""
from __future__ import absolute_import
import types
from functools import wraps

from ..parser import parser, node

class LocatedNodeMixin(object):
    """
    Adds location information for abstract syntax tree nodes.
    """
    def __init__(self, *args, **kwargs):
        super(LocatedNodeMixin, self).__init__(*args, **kwargs)
        self._method_cache = {}

    def get_next_locator(self):
        token = self.token_stream.peek()
        return token.locator

    def wrap_method(self, method):
        """
        Create a new parse method that adds locator information to the node
        it returns.
        """
        @wraps(method)
        def wrapped(self, *args, **kwargs):
            locator = self.get_next_locator()
            result = method(*args, **kwargs)
            if isinstance(result, node.Node):
                result.locator = locator
            return result
        return types.MethodType(wrapped, self)

    def __getattribute__(self, name):
        cache = super(LocatedNodeMixin, self).__getattribute__('_method_cache')
        if name in cache:
            return cache[name]
        elif name.startswith('parse_'):
            original = object.__getattribute__(self, name)
            wrapped = self.wrap_method(original)
            cache[name] = wrapped
            return wrapped
        return super(LocatedNodeMixin, self).__getattribute__(name)

class LocatorParser(LocatedNodeMixin, parser.Parser):
    """
    Concrete implementation of a location tracking parser.
    """
    pass

#
# Utility functions
#

def make_string_parser(string, filename=None, line=0, column=0, encoding='utf-8'):
    """
    Make a parser for a string that produces nodes with location information.
    """
    from ..parser.scanner import make_string_scanner, TokenStreamAllowReserved
    scanner = make_string_scanner(
        string, filename, line, column, encoding
    )
    stream = TokenStreamAllowReserved(scanner)
    return LocatorParser(stream)

def parse_string(string, filename=None, line=0, column=0, encoding='utf-8'):
    """
    Parse a string into an abstract syntax tree whose nodes have location information.
    """
    parse = make_string_parser(
        string, filename, line, column, encoding
    )
    return parse.parse()

def make_file_parser(fd, filename=None, line=0, column=0, encoding='utf-8'):
    """
    Make a parser for a file that produces nodes with location information.
    """
    from ..parser.scanner import make_file_scanner, TokenStreamAllowReserved
    scanner = make_file_scanner(
        fd, filename, line, column, encoding
    )
    stream = TokenStreamAllowReserved(scanner)
    return LocatorParser(stream)

def parse_file(filename, line=0, column=0, encoding='utf-8'):
    """
    Parse a file into an abstract syntax tree whose nodes have location information.
    """
    fd = open(filename, 'rb')
    parse = make_file_parser(fd, filename, line, column, encoding)
    return parse.parse()
