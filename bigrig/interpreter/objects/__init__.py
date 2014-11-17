"""
Specification objects for ECMAScript objects and their properties.
"""
from ..types import (
    Undefined, Null, BooleanType, NumberType, StringType, ObjectType,
    get_primitive_type
)
from ..exceptions import ESTypeError

class PropertyDescriptor(object):
    """
    Structure containing property flags and value or get/set functions.
    """
    # 8.6.1
    def __init__(self, get=None, set=None, enumerable=None,
                 configurable=None, writable=None, value=None):
        self.get = get
        self.set = set
        self.enumerable = enumerable
        self.configurable = configurable
        self.writable = writable
        self.value = value

    @classmethod
    def clone(cls, d):
        return cls(
            get=d.get, set=d.set, enumerable=d.enumerable,
            configurable=d.configurable, writable=d.writable, value=d.value
        )

    def empty(self):
        return self.get is None and \
               self.set is None and \
               self.enumerable is None and \
               self.configurable is None and \
               self.writable is None and \
               self.value is None
        

def is_accessor_descriptor(descriptor):
    """
    Descriptor contains get/set functions.
    """
    # 8.10.1
    if descriptor is Undefined:
        return False
    if descriptor.get is None and descriptor.set is None:
        return False
    return True


def is_data_descriptor(descriptor):
    """
    Descriptor contains a value.
    """
    # 8.10.2
    if descriptor is Undefined:
        return False
    if descriptor.value is None and descriptor.writable is None:
        return False
    return True


def is_generic_descriptor(descriptor):
    """
    Descriptor is uninitialized.
    """
    # 8.10.3
    if descriptor is Undefined:
        return False
    if is_accessor_descriptor(descriptor) is False and is_data_descriptor(descriptor) is False:
        return True
    return False


def from_property_descriptor(interpreter, descriptor):
    """
    Turn a ``PropertyDescriptor`` into an ``Object``.
    """
    # 8.10.4
    if descriptor is Undefined:
        return Undefined
    obj = interpreter.ObjectConstructor.construct([])
    def define(name, value):
        desc = PropertyDescriptor(
            value=value, writable=True, enumerable=True, configurable=True
        )
        obj.define_own_property(name, desc, False)
    if is_data_descriptor(descriptor):
        define('value', descriptor.value)
        define('writable', descriptor.writable)
    else:
        define('get', descriptor.get)
        define('set', descriptor.set)
    define('enumerable', descriptor.enumerable)
    define('configurable', descriptor.configurable)
    return obj


def to_property_descriptor(interpreter, obj):
    """
    Turn an ``Object`` into a ``PropertyDescriptor``.
    """
    # 8.10.5
    # assert is object
    if get_primitive_type(obj) is not ObjectType:
        raise ESTypeError('Cannot convert to property descriptor')
    desc = PropertyDescriptor()
    if obj.has_property('enumerable'):
        enum = obj.get('enumerable')
        desc.enumerable = interpreter.to_boolean(enum)
    if obj.has_property('configurable'):
        conf = obj.get('configurable')
        desc.configurable = interpreter.to_boolean(conf)
    if obj.has_property('value'):
        value = obj.get('value')
        desc.value = value
    if obj.has_property('writable'):
        writable = obj.get('writable')
        desc.writable = interpreter.to_boolean(writable)
    accessor = False
    if obj.has_property('get'):
        getter = obj.get('get')
        if not is_callable(getter) and getter is not Undefined:
            raise ESTypeError()
        accessor = True
        desc.get = getter
    if obj.has_property('set'):
        setter = obj.get('set')
        if not is_callable(setter) and setter is not Undefined:
            raise ESTypeError()
        accessor = True
        desc.set = setter
    if accessor and (desc.value is not None or desc.writable is not None):
        raise ESTypeError()
    return desc


def is_callable(value):
    """
    Is ``value`` a callable ``Object``?
    """
    if isinstance(value, ObjectType) and hasattr(value, 'call') and callable(value.call):
        return True
    return False
