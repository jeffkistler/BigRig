"""
The debugging console built-in.

This is non-standard.
"""
import sys
from .base import ObjectInstance
from .function import define_native_method
from ..types import Undefined


class ConsoleObject(ObjectInstance):
    """
    The debug console object.
    """
    es_class = 'Console'
    def __init__(self, interpreter):
        super(ConsoleObject, self).__init__(interpreter)
        define_native_method(self, 'log', self.log_method)

    def log_method(self, this, arguments):
        """
        Print the given arguments to stdout.
        """
        # TODO: format string support
        to_string = self.interpreter.to_string
        string = u' '.join(to_string(arg) for arg in arguments)
        sys.stdout.write(string + '\n')
        return Undefined
