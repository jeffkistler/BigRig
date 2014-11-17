"""
Primitive types and type conversions.
"""
import math
from itertools import izip_longest
from .exceptions import ESTypeError, ESSyntaxError
from .literals import NumberLiteralParser


NaN = float('nan')
inf = float('inf')
sign = lambda x: math.copysign(1, x)
MASK16 = (2 ** 16) - 1
MASK32 = (2 ** 32) - 1


class Type(object):
    """
    Base type class.
    """
    pass


class PrimitiveType(Type):
    """
    Base for all primitive object types.
    """
    pass


class UndefinedType(PrimitiveType):
    """
    The ``undefined`` type.
    """
    pass

# The single instance of UndefinedType
Undefined = UndefinedType()


class NullType(PrimitiveType):
    """
    The ``null`` type.
    """
    pass

# The single instance of NullType
Null = NullType()


class BooleanType(PrimitiveType):
    """
    The ``Boolean`` primitive type.
    """
    pass


class NumberType(PrimitiveType):
    """
    The ``Number`` primitive type.
    """
    pass


class StringType(PrimitiveType):
    """
    The ``String`` primitive type.
    """
    pass


class ObjectType(Type):
    """
    The base for all non-primitive objects.
    """
    pass


def get_primitive_type(obj):
    """
    Returns the primitive type class of the given object.
    """
    if obj is Undefined or obj is None:
        return Undefined
    elif obj is Null:
        return Null
    elif isinstance(obj, (bool, BooleanType)):
        return BooleanType
    elif isinstance(obj, (float, int, long, NumberType)):
        return NumberType
    elif isinstance(obj, (basestring, StringType)):
        return StringType
    return ObjectType


def is_primitive(obj):
    """
    Does the given object have a non-ObjectType primitive type class?
    """
    return get_primitive_type(obj) is not ObjectType


def check_object_coercible(obj):
    """
    9.10
    """
    primitive_type = get_primitive_type(obj)
    if primitive_type is Undefined:
        raise ESTypeError('Cannot convert undefined to object')
    elif primitive_type is Null:
        raise ESTypeError('Cannot convert null to object')


class Conversions(object):
    """
    Interpreter mixins for performing type conversions. These rely on having
    access to constructors, so they must have the interpreter available.
    
    9.0
    """
    def to_primitive(self, value, preferred_type=None):
        """
        9.1
        """
        if is_primitive(value):
            return getattr(value, 'primitive_value', value)
        obj = self.to_object(value)
        return obj.default_value(hint=preferred_type)

    def to_boolean(self, value):
        """
        9.2
        """
        primitive_type = get_primitive_type(value)
        if primitive_type is ObjectType:
            return True
        if primitive_type is Undefined or primitive_type is Null:
            return False
        value = self.to_primitive(value)
        if primitive_type is NumberType:
            if math.isnan(value):
                return False
            return bool(value)
        elif primitive_type is BooleanType:
            return value
        elif primitive_type is StringType:
            return len(value) > 0

    def to_number(self, value):
        """
        9.3
        """
        primitive_type = get_primitive_type(value)
        if primitive_type is Undefined:
            return NaN
        elif primitive_type is Null:
            return +0
        elif primitive_type is ObjectType:
            primitive_value = self.to_primitive(value, preferred_type='Number')
            return self.to_number(primitive_value)
        primitive_value = self.to_primitive(value)
        if primitive_type is NumberType:
            return primitive_value
        elif primitive_type is BooleanType:
            return int(primitive_value)
        elif primitive_type is StringType:
            try:
                value = primitive_value.strip()
                if not value:
                    return 0
                sign = 1
                has_sign = False
                if value[0] == u'-':
                    sign = -1
                    value = value[1:]
                    has_sign = True
                elif value[0] == u'+':
                    value = value[1:]
                    has_sign = True
                if value == u'Infinity':
                    return sign * inf
                if has_sign:
                    return sign * NumberLiteralParser(value).parse_decimal_literal()
                strict = self.in_strict_code()
                return NumberLiteralParser.parse_string(value, allow_octal=not strict)
            except ESSyntaxError:
                return NaN

    def to_integer(self, value):
        """
        9.4
        """
        number = self.to_number(value)
        if math.isnan(number):
            return 0
        if number == 0 or number == +inf or number == -inf:
            return number
        return int(sign(number) * math.floor(abs(number)))

    def to_int32(self, value):
        """
        9.5
        """
        value = self.to_integer(value)
        if value == inf or value == -inf or math.isnan(value) or value == 0:
            return 0
        if value & (1 << (32 - 1)):
            value = value | ~MASK32
        else:
            value = value & MASK32
        return value

    def to_uint32(self, value):
        """
        9.6
        """
        value = self.to_integer(value)
        if value == inf or value == -inf or math.isnan(value) or value == 0:
            return 0
        return MASK32 & value

    def to_uint16(self, value):
        """
        9.7
        """
        value = self.to_integer(value)
        if value == inf or value == -inf or math.isnan(value) or value == 0:
            return 0
        return MASK16 & value

    def to_string(self, value):
        """
        9.8
        """
        primitive_type = get_primitive_type(value)
        if primitive_type is Undefined:
            return "undefined"
        elif primitive_type is Null:
            return "null"
        elif primitive_type is BooleanType:
            value = self.to_boolean(value)
            return value and "true" or "false"
        elif primitive_type is NumberType:
            value = self.to_primitive(value)
            if math.isnan(value):
                return "NaN"
            elif value == inf:
                return "Infinity"
            elif value < 0:
                return "-" + self.to_string(abs(value))
            # FIXME
            return unicode(value)
        elif primitive_type is StringType:
            return self.to_primitive(value)
        elif primitive_type is ObjectType:
            primitive_value = self.to_primitive(value, preferred_type='String')
            return self.to_string(primitive_value)

    def to_object(self, value):
        """
        9.9
        """
        check_object_coercible(value)
        primitive_type = get_primitive_type(value)
        if primitive_type is ObjectType:
            return value
        # We've got a primitive, so make an object
        primitive_value = self.to_primitive(value)
        if primitive_type is BooleanType:
            cons = self.BooleanConstructor.construct
        elif primitive_type is NumberType:
            cons = self.NumberConstructor.construct
        elif primitive_type is StringType:
            cons = self.StringConstructor.construct
        return cons([primitive_value])

    def same_value(self, x, y):
        """
        9.12
        """
        x_type = get_primitive_type(x)
        y_type = get_primitive_type(y)
        if x_type != y_type:
            return False
        if x_type is Undefined:
            return True
        if x_type is Null:
            return True
        if x_type is NumberType:
            x = self.to_primitive(x)
            y = self.to_number(y)
            if math.isnan(x) and math.isnan(y):
                return True
            return x == y
        elif x_type is StringType:
            x = self.to_primitive(x)
            y = self.to_string(y)
            return x == y
        elif x_type is BooleanType:
            x = self.to_primitive(x)
            y = self.to_boolean(y)
            return x == y
        elif x_type is ObjectType and y_type is ObjectType:
            return id(x) == id(y)
        return False


def get_arguments(arguments, count=1):
    """
    Return the argument or ``Undefined``. If ``count`` is > 1, return
    an array of the arguments or ``Undefined`` up to ``count`` elements.
    """
    to_return = arguments[:count]
    undefined_count = max(count - len(arguments), 0)
    to_return.extend([Undefined for i in range(undefined_count)])
    if count == 1:
        to_return = to_return[0]
    return to_return
