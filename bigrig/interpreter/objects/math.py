"""
Specification object for the ``Math`` built-in.
"""
from __future__ import absolute_import
import math
import random
from .base import ObjectInstance
from .function import define_native_method

NaN = float('nan')

class MathObject(ObjectInstance):
    """
    The ``Math`` built-in object class.

    15.8
    """
    es_class = 'Math'

    def __init__(self, interpreter):
        super(MathObject, self).__init__(interpreter)
        self.prototype = interpreter.ObjectPrototype
        self.set_property('E', math.e)
        self.set_property('LN10', math.log(10))
        self.set_property('LN2', math.log(2))
        self.set_property('LOG2E', math.log(math.e, 2))
        self.set_property('LOG10E', math.log10(math.e))
        self.set_property('PI', math.pi)
        self.set_property('SQRT1_2', math.sqrt(0.5))
        self.set_property('SQRT2', math.sqrt(2))
        define_native_method(self, 'abs', self.abs_method, 1)
        define_native_method(self, 'acos', self.acos_method, 1)
        define_native_method(self, 'asin', self.asin_method, 1)
        define_native_method(self, 'atan', self.atan_method, 1)
        define_native_method(self, 'atan2', self.atan2_method, 2)
        define_native_method(self, 'ceil', self.ceil_method, 1)
        define_native_method(self, 'cos', self.cos_method, 1)
        define_native_method(self, 'exp', self.exp_method, 1)
        define_native_method(self, 'floor', self.floor_method, 1)
        define_native_method(self, 'log', self.log_method, 1)
        define_native_method(self, 'max', self.max_method, 2)
        define_native_method(self, 'min', self.min_method, 2)
        define_native_method(self, 'pow', self.pow_method, 1)
        define_native_method(self, 'random', self.random_method)
        define_native_method(self, 'round', self.round_method, 1)
        define_native_method(self, 'sin', self.sin_method, 1)
        define_native_method(self, 'sqrt', self.sqrt_method, 1)
        define_native_method(self, 'tan', self.tan_method, 1)

    def number_args(self, arguments, count=1):
        """
        """
        coerced = []
        to_number = self.interpreter.to_number
        num_args = len(arguments)
        if num_args == 1:
            return to_number(arguments[0])
        elif count is None:
            return [to_number(arg) for arg in arguments]
        for i in range(count):
            if i <= num_args:
                coerced.append(to_number(arguments[i]))
            else:
                coerced.append(NaN)
        return coerced

    def abs_method(self, this, arguments):
        """
        ``Math.abs`` method implementation.

        15.8.2.1
        """
        x = self.number_args(arguments)
        return abs(x)

    def acos_method(self, this, arguments):
        """
        ``Math.acos`` method implementation.

        15.8.2.2
        """
        x = self.number_args(arguments)
        if math.isnan(x) or x < -1 or x > 1:
            return NaN
        return math.acos(x)

    def asin_method(self, this, arguments):
        """
        ``Math.asin`` method implementation.

        15.8.2.3
        """
        x = self.number_args(arguments)
        if math.isnan(x) or x < -1 or x > 1:
            return NaN
        return math.asin(x)

    def atan_method(self, this, arguments):
        """
        ``Math.atan`` method implementation.

        15.8.2.4
        """
        x = self.number_args(arguments)
        if math.isnan(x) or x < -1 or x > 1:
            return NaN
        elif x == float('-inf'):
            return -math.pi / 2.0
        elif x == float('inf'):
            return math.pi / 2.0
        return math.atan(x)

    def atan2_method(self, this, arguments):
        """
        ``Math.atan2`` method implementation.

        15.8.2.5
        """
        y, x = self.number_args(arguments, 2)
        return math.atan2(y, x)

    def ceil_method(self, this, arguments):
        """
        ``Math.ceil`` method implementation.

        15.8.2.6
        """
        x = self.number_args(arguments)
        return math.ceil(x)

    def cos_method(self, this, arguments):
        """
        ``Math.cos`` method implementation.

        15.8.2.7
        """
        x = self.number_args(arguments)
        if math.isnan(x) or x == float('-inf') or x == float('inf'):
            return NaN
        return math.cos(x)

    def exp_method(self, this, arguments):
        """
        ``Math.exp`` method implementation.

        15.8.2.8
        """
        x = self.number_args(arguments)
        if math.isnan(x):
            return NaN
        elif x == float('-inf'):
            return 0
        elif x == float('inf'):
            return float('inf')
        return math.exp(x)

    def floor_method(self, this, arguments):
        """
        ``Math.floor`` method implementation.

        15.8.2.9
        """
        x = self.number_args(arguments)
        return math.floor(x)

    def log_method(self, this, arguments):
        """
        ``Math.log`` method implementation.

        15.8.2.10
        """
        x = self.number_args(arguments)
        if math.isnan(x) or x < 0:
            return NaN
        if x == 0:
            return float('-inf')
        return math.log(x)

    def max_method(self, this, arguments):
        """
        ``Math.max`` method implementation.

        15.8.2.11
        """
        args = self.number_args(arguments, count=None)
        return max(args)

    def min_method(self, this, arguments):
        """
        ``Math.min`` method implementation.

        15.8.2.12
        """
        args = self.number_args(arguments, count=None)
        return min(args)

    def pow_method(self, this, arguments):
        """
        ``Math.pow`` method implementation.

        15.8.2.13
        """
        x, y = self.number_args(arguments, count=2)
        return math.pow(x, y)

    def random_method(self, this, arguments):
        """
        ``Math.random`` method implementation.

        15.8.2.14
        """
        return random.random()

    def round_method(self, this, arguments):
        """
        ``Math.round`` method implementation.

        15.8.2.15
        """
        x = self.number_args(arguments)
        if math.isnan(x):
            return NaN
        return math.floor(x + 0.5)

    def sin_method(self, this, arguments):
        """
        ``Math.sin`` method implementation.

        15.8.2.16
        """
        x = self.number_args(arguments)
        if math.isnan(x) or x == float('-inf') or x == float('inf'):
            return NaN
        return math.sin(x)

    def sqrt_method(self, this, arguments):
        """
        ``Math.sqrt`` method implementation.

        15.8.2.17
        """
        x = self.number_args(arguments)
        if math.isnan(x) or x < 0:
            return NaN
        return math.sqrt(x)

    def tan_method(self, this, arguments):
        """
        ``Math.tan`` method implementation.

        15.8.2.18
        """
        x = self.number_args(arguments)
        if math.isnan(x) or x == float('-inf') or x == float('inf'):
            return NaN
        return math.tan(x)
