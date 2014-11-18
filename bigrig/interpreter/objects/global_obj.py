"""
The specification object for the built-in global context object.
"""
from __future__ import absolute_import
import math
import urllib
from .base import ObjectInstance
from .function import define_native_method
from ..types import NaN, inf, Undefined, get_arguments


class GlobalObject(ObjectInstance):
    """
    The built-in object that contains the other built-in objects.

    15.1
    """
    es_class = "Global"

    def __init__(self, interpreter):
        super(GlobalObject, self).__init__(interpreter)
        # Use the object prototype. As per 15.1 it's up to us.
        prototype = interpreter.ObjectPrototype
        self.prototype = prototype
        self.set_property('prototype', prototype)
        self.set_property('NaN', NaN)
        self.set_property('Infinity', inf)
        self.set_property('undefined', Undefined)
        define_native_method(self, 'parseInt', self.parse_int_method, 2)
        define_native_method(self, 'parseFloat', self.parse_float_method, 1)
        define_native_method(self, 'isNaN', self.is_nan_method, 1)
        define_native_method(self, 'isFinite', self.is_finite_method, 1)
        define_native_method(self, 'parseInt', self.decode_uri_method, 1)
        define_native_method(self, 'decodeURIComponent', self.decode_uri_component_method, 1)
        define_native_method(self, 'encodeURI', self.encode_uri_method, 1)
        define_native_method(self, 'encodeURIComponent', self.encode_uri_component_method, 1)

    def parse_int_method(self, this, arguments):
        """
        ``parseInt`` global function implementation.

        15.1.2.2
        """
        string, radix = get_arguments(arguments, count=2)
        string = self.interpreter.to_string(string)
        radix = self.interpreter.to_uint32(radix)
        string = string.lstrip()
        sign = 1
        if string.startswith('-'):
            sign = -1
            string = string[1:]
        elif string.startswith('+'):
            string = string[1:]
        if radix == 0 or radix == 16:
            if string.startswith('0x') or string.startswith('0X'):
                radix = 16
                string = string[2:]
        if radix == 0:
            radix = 10
        elif radix < 2 or radix > 36:
            return NaN
        number = int(string, radix)
        return sign * number

    def parse_float_method(self, this, arguments):
        """
        ``parseFloat`` global function implementation.

        15.1.2.3
        """
        string = get_arguments(arguments, count=1)
        string = self.interpreter.to_string(string)
        string = string.lstrip()
        try:
            value = float(string)
        except ValueError:
            return NaN
        return value

    def is_nan_method(self, this, arguments):
        """
        ``isNaN`` global function implementation.

        15.1.2.4
        """
        number = get_arguments(arguments, count=1)
        return math.isnan(self.interpreter.to_number(number))

    def is_finite_method(self, this, arguments):
        """
        ``isFinite`` global function implementation.

        15.1.2.5
        """
        number = get_arguments(arguments, count=1)
        number = self.interpreter.to_number(number)
        if math.isnan(number) or number == float('inf') or number == float('-inf'):
            return False
        return True

    def decode_uri_method(self, this, arguments):
        """
        ``decodeURI`` global function implementation.

        15.1.2.6
        """
        string = get_arguments(arguments, count=1)
        string = self.interpreter.to_string(string)
        return urllib.unquote(string)

    def decode_uri_component_method(self, this, arguments):
        """
        ``decodeURIComponent`` global function implementation.

        15.1.2.7
        """
        string = get_arguments(arguments, count=1)
        string = self.interpreter.to_string(string)
        return urllib.unquote(string)

    def encode_uri_method(self, this, arguments):
        """
        ``encodeURI`` global function implementation.

        15.1.2.8
        """
        string = get_arguments(arguments, count=1)
        string = self.interpreter.to_string(string)
        return urllib.quote(string.encode('utf-8'), safe='~@#$&()*!+=:;,.?/\'')

    def encode_uri_component_method(self, this, arguments):
        """
        ``encodeURIComponent`` global function implementation.

        15.1.2.9
        """
        string = get_arguments(arguments, count=1)
        string = self.interpreter.to_string(string)
        return urllib.quote(string.encode('utf-8'), safe='~()*!.\'')
