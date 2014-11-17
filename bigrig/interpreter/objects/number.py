"""
Specification objects for the ``Number`` built-in.
"""
from __future__ import absolute_import
import math
import sys
from .object import ObjectInstance, FunctionInstance
from .function import define_native_method
from ..types import NumberType, Undefined, get_arguments, NaN, inf, get_primitive_type
from ..exceptions import ESTypeError, ESRangeError

NUMBER_DIGITS = '0123456789abcdefghijklmnopqrstuvwxyz'


class NumberInstance(ObjectInstance, NumberType):
    """
    Specialized ``Number`` object class.
    """
    es_class = "Number"

    def __init__(self, interpreter, primitive_value):
        super(NumberInstance, self).__init__(interpreter)
        self.primitive_value = primitive_value


class NumberConstructor(FunctionInstance):
    """
    The ``Number`` constructor function.

    15.7.3
    """
    def __init__(self, interpreter):
        super(NumberConstructor, self).__init__(interpreter)
        self.prototype = interpreter.FunctionPrototype
        self.set_property('length', 1)
        self.set_property('MAX_VALUE', sys.float_info.max)
        self.set_property('MIN_VALUE', sys.float_info.min)
        self.set_property('NaN', NaN)
        self.set_property('NEGATIVE_INFINITY', -inf)
        self.set_property('POSITIVE_INFINITY', inf)

    def call(self, this, arguments):
        """
        15.7.1.1
        """
        if arguments:
            return self.interpreter.to_number(arguments[0])
        return 0

    def construct(self, arguments):
        """
        15.7.2.1
        """
        value = self.call(None, arguments)
        obj = NumberInstance(self.interpreter, value)
        obj.prototype = self.interpreter.NumberPrototype
        obj.extensible = True
        return obj


class NumberPrototype(NumberInstance):
    """
    The prototype object assigned to ``Number`` instances.

    15.7.4
    """
    def __init__(self, interpreter):
        super(NumberPrototype, self).__init__(interpreter, 0)
        self.prototype = interpreter.ObjectPrototype
        define_native_method(self, 'toString', self.to_string_method)
        define_native_method(self, 'toLocaleString', self.to_locale_string_method)
        define_native_method(self, 'valueOf', self.value_of_method)
        define_native_method(self, 'toFixed', self.to_fixed_method, 1)
        define_native_method(self, 'toExponential', self.to_exponential_method, 1)
        define_native_method(self, 'toPrecision', self.to_precision_method, 1)

    def to_base(self, x, base):
        """
        """
        if x == 0:
            return NUMBER_DIGITS[0]
        negative = False
        if x < 0:
            negative = True
            x = -x
        converted = []
        while x > 0:
            index = x % base
            converted.append(NUMBER_DIGITS[index])
            x = int(x // base)
        if negative:
            converted.append('-')
        return u''.join(reversed(converted))

    def to_base_fraction(self, x, base):
        """
        """
        if x == 0:
            return 0
        converted = []
        remainder = x
        while remainder > 0 and len(converted) < 20:
            coeff = remainder * base
            index = long(coeff)
            remainder = coeff - index
            converted.append(NUMBER_DIGITS[index])
        return u''.join(converted)

    #
    # Method property implementations
    #

    def to_string_method(self, this, arguments):
        """
        ``Number.prototype.toString`` method implementation.

        15.7.4.1
        """
        if get_primitive_type(this) is not NumberType:
            raise ESTypeError('Number.prototype.toString is not generic')
        x = self.interpreter.to_number(this)
        if math.isnan(x):
            return 'NaN'
        elif x == inf:
            return 'Infinity'
        elif x == -inf:
            return '-Infinity'
        radix = get_arguments(arguments, count=1)
        if radix is Undefined:
            radix = 10
        else:
            radix = self.interpreter.to_integer(radix)
            if not radix >= 2 and radix <= 36:
                raise ESRangeError('radix must be in the range 2 through 36')
        if radix == 10:
            return unicode(x)
        # Change base
        integer = long(x)
        fraction = x - integer
        result = self.to_base(x, radix)
        if fraction:
            result = '%s.%s' % (integer, self.to_base_fraction(x, radix))
        return result

    def to_locale_string_method(self, this, arguments):
        """
        ``Number.prototype.toLocaleString`` method implementation.

        15.7.4.1
        """
        return self.to_string(this, arguments)

    def value_of_method(self, this, arguments):
        """
        ``Number.prototype.valueOf`` method implementation.

        15.7.4.2
        """
        if get_primitive_type(this) is not NumberType:
            raise ESTypeError('Number.prototype.valueOf is not generic')
        return self.interpreter.to_number(this)

    def to_fixed_method(self, this, arguments):
        """
        ``Number.prototype.toFixed`` method implementation.

        15.7.4.3
        """
        x = self.interpreter.to_number(this)
        if math.isnan(x):
            return 'NaN'
        fraction = get_arguments(arguments, count=1)
        f = self.interpreter.to_integer(fraction)
        if f < 0 or f > 20:
            raise ESRangeError('fractionDigits must be in range 0 to 20')
        format_str = '{:.%df}' % f
        return format_str.format(x)

    def to_exponential_method(self, this, arguments):
        """
        ``Number.prototype.toExponential`` method implementation.

        15.7.4.4
        """
        x = self.interpreter.to_number(this)
        if math.isnan(x):
            return 'NaN'
        elif x == float('inf'):
            return 'Infinity'
        elif x == float('-inf'):
            return '-Infinity'
        fraction = get_arguments(arguments, count=1)
        f = self.interpreter.to_integer(fraction)
        format_str = '{:.%de}' % f
        return format_str.format(x)

    def to_precision_method(self, this, arguments):
        """
        ``Number.prototype.toPrecision`` method implementation.

        15.7.4.5
        """
        x = self.interpreter.to_number(this)
        if math.isnan(x):
            return 'NaN'
        precision = get_arguments(arguments, count=1)
        if precision is Undefined:
            return self.interpreter.to_string(x)
        p = self.interpreter.to_integer(precision)
        format_str = '{:.%d}' % p
        return format_str.format(x)
