"""
Specification objects for ``Error`` and associated built-ins.
"""
from .base import ObjectInstance, FunctionInstance
from .function import define_native_method
from ..types import ObjectType, Undefined, get_arguments, get_primitive_type
from ..exceptions import ESTypeError


class ErrorInstance(ObjectInstance):
    """
    The specialized base ``Error`` object class.

    15.11
    """
    es_class = "Error"

    def __init__(self, interpreter, name):
        super(ErrorInstance, self).__init__(interpreter)
        self.name = name
        self.set_property('name', name, writable=True, configurable=True)


class ErrorConstructor(FunctionInstance):
    """
    A base for ``Error`` object constructor functions.
    """
    def __init__(self, interpreter, name):
        super(ErrorConstructor, self).__init__(interpreter)
        self.name = name
        self.set_property('length', 1)

    def call(self, this, arguments):
        """
        15.11.1.1
        """
        return self.construct(arguments)

    def construct(self, arguments):
        """
        15.11.2.1
        """
        message = get_arguments(arguments, count=1)
        obj = ErrorInstance(self.interpreter, self.name)
        obj.es_class = self.name
        obj.prototype = self.get('prototype')
        if message is not Undefined:
            obj.set_property('message', self.interpreter.to_string(message))
        return obj


class ErrorPrototype(ObjectInstance):
    """
    The base for error prototype objects.

    15.11.4
    """
    def __init__(self, interpreter, name):
        super(ErrorPrototype, self).__init__(interpreter)
        self.name = name
        self.set_property('name', name)
        self.set_property('message', '')
        define_native_method(self, 'toString', self.to_string_method)

    def to_string_method(self, this, arguments):
        """
        15.11.4.4
        """
        if get_primitive_type(this) is not ObjectType:
            raise ESTypeError('Error.prototype.toString applied to a non-object')
        name =  this.get('name')
        if name is Undefined:
            name = 'Error'
        else:
            name = self.interpreter.to_string(name)
        message = this.get('message')
        if message is not Undefined:
            message = self.interpreter.to_string(message)
        else:
            message = ''
        if name == '':
            return message
        elif message == '':
            return name
        return u'%s: %s' % (name, message)


def create_error(interpreter, name):
    """
    Construct, configure and return an error constructor for the built-in error
    class with the given name.
    """
    constructor = ErrorConstructor(interpreter, name)
    constructor.prototype = interpreter.FunctionPrototype
    error_prototype = ErrorPrototype(interpreter, name)
    if name != 'Error':
        error_prototype.prototype = interpreter.ErrorConstructor.get('prototype')
    else:
        error_prototype.prototype = interpreter.ObjectConstructor.get('prototype')
    constructor.set_property('prototype', error_prototype)
    return constructor
