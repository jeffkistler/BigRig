"""
Classes for the basic ES Object instances.
"""
from ..types import ObjectType, Undefined, get_primitive_type, is_primitive
from ..exceptions import ESTypeError
from . import (
    PropertyDescriptor, is_callable, is_data_descriptor,
    is_accessor_descriptor, is_generic_descriptor
)


class ObjectInstance(ObjectType):
    """
    The basic internal class type for objects.

    8.6
    """
    es_class = "Object"
    prototype = None
    extensible = True

    def __init__(self, interpreter):
        self.interpreter = interpreter
        self.properties = {} # Mapping of unicode to PropertyDescriptor

    #
    # Internal Specification Methods
    #

    def get_own_property(self, name):
        """
        8.12.1
        """
        if name not in self.properties:
            return Undefined
        return self.properties[name]

    def get_property(self, name):
        """
        8.12.2
        """
        prop = self.get_own_property(name)
        if prop is not Undefined:
            return prop
        if self.prototype is not None:
            return self.prototype.get_property(name)
        return Undefined

    def get(self, name):
        """
        8.12.3
        """
        desc = self.get_property(name)
        if desc is Undefined:
            return Undefined
        if is_data_descriptor(desc):
            return desc.value
        else:
            getter = desc.get
            if getter is Undefined or getter is None:
                return Undefined
            return getter.call(self, [])

    def can_put(self, name):
        """
        8.12.4
        """
        desc = self.get_own_property(name)
        if desc is not Undefined:
            if is_accessor_descriptor(desc):
                if desc.set is None:
                    return False
                return True
            else:
                return desc.writable
        prototype = self.prototype
        if prototype is None:
            return self.extensible
        inherited = prototype.get_property(name)
        if inherited is Undefined:
            return self.extensible
        if is_accessor_descriptor(inherited):
            if inherited.set is None:
                return False
            return True
        else:
            if not self.extensible:
                return False
            return inherited.writable

    def put(self, name, value, throw=False):
        """
        8.12.5
        """
        if not self.can_put(name):
            if throw:
                raise ESTypeError('%s is not a writable property' % name)
            return
        own_desc = self.get_own_property(name)
        if is_data_descriptor(own_desc):
            value_desc = PropertyDescriptor(value=value)
            self.define_own_property(name, value_desc, throw=throw)
            return
        desc = self.get_property(name)
        if is_accessor_descriptor(desc):
            setter = desc.set
            setter.call(self, [value])
        else:
            new_desc = PropertyDescriptor(
                value=value, writable=True, enumerable=True, configurable=True
            )
            self.define_own_property(name, new_desc, throw=throw)

    def has_property(self, name):
        """
        8.12.6
        """
        desc = self.get_property(name)
        if desc is Undefined:
            return False
        return True

    def delete(self, name, throw=False):
        """
        8.12.7
        """
        desc = self.get_own_property(name)
        if desc is Undefined:
            return True
        if desc.configurable:
            del self.properties[name]
            return True
        elif throw:
            raise ESTypeError('Cannot delete property %s' % name)
        return False

    def default_value(self, hint='Number'):
        """
        8.12.8
        """
        if hint is None:
            hint = 'Number'
        if hint == 'String':
            to_string = self.get('toString')
            if is_callable(to_string):
                string = to_string.call(self, [])
                if is_primitive(string):
                    return string
            value_of = self.get('valueOf')
            if is_callable(value_of):
                val = value_of.call(self, [])
                if is_primitive(val):
                    return val
        elif hint == 'Number':
            value_of = self.get('valueOf')
            if is_callable(value_of):
                val = value_of.call(self, [])
                if is_primitive(val):
                    return val
            to_string = self.get('toString')
            if is_callable(to_string):
                string = to_string.call(self, [])
                if is_primitive(string):
                    return string
        raise ESTypeError('Cannot convert to %s' % hint)

    def define_own_property(self, name, descriptor, throw=False):
        """
        8.12.9
        """
        same_value = self.interpreter.same_value
        def reject(message='Invalid property assignment'):
            if throw:
                raise ESTypeError(message)
            return False
        current = self.get_own_property(name)
        extensible = self.extensible
        if current is Undefined:
            if not extensible:
                return reject('Cannot define property on non-extensible object')
            self.properties[name] = PropertyDescriptor.clone(descriptor)
            return True
        if descriptor.empty():
            return True
        if current.enumerable is descriptor.enumerable and \
           current.configurable is descriptor.configurable and \
           current.writable is descriptor.writable:
            if same_value(current.get, descriptor.get) and \
               same_value(current.set, descriptor.set) and \
               same_value(current.value, descriptor.value):
                return True
        if not current.configurable:
            if descriptor.configurable:
                return reject()
            elif descriptor.enumerable and not current.enumerable == descriptor.enumerable:
                return reject()
        elif is_generic_descriptor(descriptor):
            # No further validation needed
            pass
        elif is_data_descriptor(current) != is_data_descriptor(descriptor):
            if not current.configurable:
                return reject()
            current = PropertyDescriptor.clone(current)
            if is_data_descriptor(current):
                current.get = Undefined
                current.set = Undefined
            else:
                current.get = None
                current.set = None
                current.writable = None
                current.value = Undefined
            self.properties[name] = current
        elif is_data_descriptor(current) and is_data_descriptor(descriptor):
            # 10
            if not current.configurable:
                if not current.writable:
                    if descriptor.writable:
                        return reject()
                    if descriptor.value is not None and not same_value(descriptor.value, current.value):
                        return reject()
        else: # is_accessor_descriptor(current) and is_accessor_descriptor(descriptor):
            # 11
            if not current.configurable:
                if not same_value(descriptor.set, current.set):
                    return reject()
                if not same_value(descriptor.get, current.get):
                    return reject()
        if descriptor.value is not None:
            current.value = descriptor.value
        if descriptor.writable is not None:
            current.writable = descriptor.writable
        if descriptor.enumerable is not None:
            current.enumerable = descriptor.writable
        if descriptor.configurable is not None:
            current.configurable = descriptor.configurable
        if descriptor.get is not None:
            current.get = descriptor.get
        if descriptor.set is not None:
            current.set = descriptor.set
        return True

    #
    # Helper methods
    #

    def set_property(self, name, value, writable=False, enumerable=False, configurable=False):
        """
        Internal use only property setter. This does not perform descriptor checks.
        """
        desc = PropertyDescriptor(
            value=value, enumerable=enumerable, writable=writable,
            configurable=configurable
        )
        self.properties[name] = desc


class FunctionInstance(ObjectInstance):
    """
    The base internal object class for function objects.

    15.3.5 & 13.2
    """
    es_class = "Function"

    def call(self, this, arguments):
        """
        The internal function invocation.
        """
        raise NotImplementedError()

    def has_instance(self, value):
        """
        15.3.5.3
        """
        if get_primitive_type(value) is not ObjectType:
            return False
        o = self.get('prototype')
        if get_primitive_type(o) is not ObjectType:
            raise ESTypeError('Invalid prototype property')
        value = value.prototype
        while o is not value:
            if value is None:
                return False
            value = value.prototype
        return True

    def get(self, name):
        """
        15.3.5.4
        """
        value = super(FunctionInstance, self).get(name)
        if name == 'caller' and getattr(value, 'strict', False):
            raise ESTypeError("'caller' is not accessible in strict mode")
        return value
