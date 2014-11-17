"""
Specification objects for the ``Boolean`` built-in.
"""
from .base import ObjectInstance, FunctionInstance
from .function import define_native_method
from ..types import BooleanType, get_arguments, get_primitive_type
from ..exceptions import ESTypeError

class BooleanInstance(ObjectInstance, BooleanType):
    """
    The specialized ``Boolean`` object class.

    15.6.5
    """
    es_class = "Boolean"

    def __init__(self, interpreter, primitive_value):
        super(BooleanInstance, self).__init__(interpreter)
        self.primitive_value = primitive_value


class BooleanConstructor(FunctionInstance):
    """
    The ``Boolean`` constructor function.

    15.6.1.1 & 15.6.1.2
    """
    def __init__(self, interpreter):
        super(BooleanConstructor, self).__init__(interpreter)
        self.prototype = interpreter.FunctionPrototype
        self.set_property('length', 1)

    def call(self, this, arguments):
        """
        Return the boolean primitive value of the given object.

        15.6.1.1
        """
        return self.interpreter.to_boolean(get_arguments(arguments, count=1))

    def construct(self, arguments):
        """
        Build and return the specialized ``Boolean`` object instance.

        15.6.1.2
        """
        value = self.interpreter.to_boolean(get_arguments(arguments, count=1))
        obj = BooleanInstance(self.interpreter, value)
        obj.prototype = self.interpreter.BooleanPrototype
        return obj


class BooleanPrototype(BooleanInstance):
    """
    The prototype object assigned to ``Boolean`` instances.
    """
    def __init__(self, interpreter):
        super(BooleanPrototype, self).__init__(interpreter, False)
        self.prototype = interpreter.ObjectPrototype
        define_native_method(self, 'toString', self.to_string_method)
        define_native_method(self, 'valueOf', self.value_of_method)

    def to_string_method(self, this, arguments):
        """
        ``Boolean.prototype.toString`` method implementation.

        15.6.4.2
        """
        b = this
        primitive_type = get_primitive_type(b)
        if primitive_type is BooleanType:
            b = self.interpreter.to_primitive(b)
        elif primitive_type == ObjectType and b.es_class == 'Boolean':
            b = b.primitive_value
        else:
            raise ESTypeError('Boolean.prototype.toString is not generic')
        return b and "true" or "false"

    def value_of_method(self, this, arguments):
        """
        ``Boolean.prototype.valueOf`` method implementation.

        15.6.4.3
        """
        b = this
        primitive_type = get_primitive_type(b)
        if primitive_type is BooleanType:
            b = self.interpreter.to_primitive(b)
        elif primitive_type == ObjectType and b.es_class == 'Boolean':
            b = b.primitive_value
        else:
            raise ESTypeError('Boolean.prototype.valueOf is not generic')
        return b
