"""
Specification objects for the ``Object`` built-in.
"""
from . import PropertyDescriptor, is_data_descriptor, to_property_descriptor, from_property_descriptor
from .base import ObjectInstance, FunctionInstance
from .function import define_native_method
from ..types import Undefined, Null, ObjectType, get_arguments, get_primitive_type
from ..exceptions import ESTypeError


class ObjectConstructor(FunctionInstance):
    """
    The ``Object`` constructor function.

    15.2.1 & 15.2.2
    """
    def __init__(self, interpreter):
        super(ObjectConstructor, self).__init__(interpreter)
        self.extensible = True
        self.prototype = interpreter.FunctionPrototype
        self.set_property('length', 1)
        define_native_method(self, 'getPrototypeOf', self.get_prototype_of_method)
        define_native_method(
            self, 'getOwnPropertyDescriptor', self.get_own_property_descriptor_method, 2
        )
        define_native_method(self, 'getOwnPropertyNames', self.get_own_property_names_method)
        define_native_method(self, 'create', self.create_method_method, 2)
        define_native_method(self, 'defineProperty', self.define_property_method, 3)
        define_native_method(self, 'defineProperties', self.define_properties_method, 2)
        define_native_method(self, 'seal', self.seal_method)
        define_native_method(self, 'freeze', self.freeze_method)
        define_native_method(self, 'preventExtensions', self.prevent_extensions_method)
        define_native_method(self, 'isSealed', self.is_sealed_method)
        define_native_method(self, 'isFrozen', self.is_frozen_method)
        define_native_method(self, 'isExtensible', self.is_extensible_method)
        define_native_method(self, 'keys', self.keys_method)

    def call(self, this, arguments):
        """
        15.2.1
        """
        value = get_arguments(arguments, count=1)
        if value is Null or value is Undefined:
            return self.construct(arguments)
        return self.interpreter.to_object(value)

    def construct(self, arguments):
        """
        15.2.2
        """
        value = get_arguments(arguments, count=1)
        if value is not Undefined and value is not Null:
            return self.interpreter.to_object(value)
        obj = ObjectInstance(self.interpreter)
        obj.prototype = self.interpreter.ObjectPrototype
        obj.es_class = 'Object'
        obj.extensible = True
        return obj

    # Helpers

    def get_arguments(self, arguments, count=1):
        """
        """
        if count == 1:
            obj = get_arguments(arguments, count=1)
            args = obj
        else:
            args = get_arguments(arguments, count=count)
            obj = args[0]
        if get_primitive_type(obj) is not ObjectType:
            string = self.interpreter.to_string(obj)
            raise ESTypeError('%s is not an object' % string)
        return args

    #
    # Method property implementations
    #

    def get_prototype_of_method(self, this, arguments):
        """
        ``Object.getPrototypeOf`` method implementation.

        15.2.3.2
        """
        obj = self.get_arguments(arguments, count=1)
        return getattr(obj, 'prototype', Null)

    def get_own_property_descriptor_method(self, this, arguments):
        """
        ``Object.getOwnPropertyDescriptor`` method implementation.

        15.2.3.3
        """
        obj, name = self.get_arguments(arguments, count=2)
        name = self.interpreter.to_string(name)
        desc = obj.get_own_property(name)
        return from_property_descriptor(self.interpreter, desc)

    def get_own_property_names_method(self, this, arguments):
        """
        ``Object.getOwnPropertyNames`` method implementation.

        15.2.3.4
        """
        obj = self.get_arguments(arguments, count=1)
        array = self.interpreter.ArrayConstructor.construct([])
        for i, name in enumerate(obj.properties):
            desc = PropertyDescriptor(
                value=name, writable=True, enumerable=True, configurable=True,
            )
            array.define_own_property(unicode(i), desc, False)
        return array

    def create_method_method(self, this, arguments):
        """
        ``Object.createMethod`` method implementation.

        15.2.3.5
        """
        o = self.get_arguments(arguments, count=1)
        obj = self.construct([])
        obj.prototype = o
        properties = len(arguments) > 1 and arguments[1] or Undefined
        if properties is not Undefined:
            self.define_properties_method(this, [obj, properties])
        return obj

    def define_property_method(self, this, arguments):
        """
        ``Object.defineProperty`` method implementation.

        15.2.3.6
        """
        obj, name, attributes = self.get_arguments(arguments, count=3)
        name = self.interpreter.to_string(name)
        desc = to_property_descriptor(self.interpreter, attributes)
        obj.define_own_property(name, desc, True)
        return obj

    def define_properties_method(self, this, arguments):
        """
        ``Object.defineProperties`` method implementation.

        15.2.3.7
        """
        obj, properties = self.get_arguments(arguments, count=2)
        properties = self.interpreter.to_object(properties)
        for name, desc in properties.properties.iteritems():
            if not desc.enumerable:
                continue
            desc_obj = properties.get(name)
            desc = to_property_descriptor(self.interpreter, desc_obj)
            obj.define_own_property(name, desc, True)
        return obj
            
    def seal_method(self, this, arguments):
        """
        ``Object.seal`` method implementation.

        15.2.3.8
        """
        obj = self.get_arguments(arguments, count=1)
        for desc in obj.properties.itervalues():
            if desc.configurable is True:
                desc.configurable = False
        obj.extensible = False
        return obj

    def freeze_method(self, this, arguments):
        """
        ``Object.freeze`` method implementation.

        15.2.3.9
        """
        obj = self.get_arguments(arguments, count=1)
        for desc in obj.properties.itervalues():
            if is_data_descriptor(desc):
                if desc.writable is True:
                    desc.writable = False
            if desc.configurable is True:
                desc.configurable = False
        obj.extensible = False
        return obj

    def prevent_extensions_method(self, this, arguments):
        """
        ``Object.preventExtensions`` method implementation.

        15.2.3.10
        """
        obj = self.get_arguments(arguments, count=1)
        obj.extensible = False
        return obj

    def is_sealed_method(self, this, arguments):
        """
        ``Object.isSealed`` method implementation.

        15.2.3.11
        """
        obj = self.get_arguments(arguments, count=1)
        for desc in obj.properties.itervalues():
            if desc.configurable is True:
                return False
        if obj.extensible is False:
            return True
        return False

    def is_frozen_method(self, this, arguments):
        """
        ``Object.isFrozen`` method implementation.

        15.2.3.12
        """
        obj = self.get_arguments(arguments, count=1)
        for desc in obj.properties.itervalues():
            if is_data_descriptor(desc):
                if desc.writable is True:
                    return False
                if desc.configurable is True:
                    return False
        if obj.extensible is False:
            return True
        return False

    def is_extensible_method(self, this, arguments):
        """
        ``Object.isExtensible`` method implementation.

        15.2.3.13
        """
        obj = self.get_arguments(arguments, count=1)
        return obj.extensible

    def keys_method(self, this, arguments):
        """
        ``Object.keys`` method implementation.

        15.2.3.14
        """
        obj = self.get_arguments(arguments, count=1)
        array = self.interpreter.ArrayConstructor.construct([])
        index = 0
        for name, desc in obj.properties.iteritems():
            if desc.enumerable is True:
                desc = PropertyDescriptor(
                    value=name, writable=True, enumerable=True, configurable=True
                )
                array.define_own_property(unicode(index), desc, False)
                index = index + 1
        return array


class ObjectPrototype(ObjectInstance):
    """
    The prototype object assigned to ``Object`` instances.

    15.2.4
    """
    prototype = None

    def __init__(self, interpreter):
        super(ObjectPrototype, self).__init__(interpreter)
        define_native_method(self, 'toString', self.to_string_method)
        define_native_method(self, 'toLocaleString', self.to_locale_string_method)
        define_native_method(self, 'valueOf', self.value_of_method)
        define_native_method(self, 'hasOwnProperty', self.has_own_property_method)
        define_native_method(self, 'isPrototypeOf', self.is_prototype_of_method)
        define_native_method(self, 'propertyIsEnumerable', self.property_is_enumerable_method)

    def to_string_method(self, this, arguments):
        """
        ``Object.prototype.toString`` method implementation.

        15.2.4.2
        """
        if this is Undefined:
            return u'[object Undefined]'
        elif this is Null:
            return u'[object Null]'
        o = self.interpreter.to_object(this)
        return u'[object %s]' % o.es_class

    def to_locale_string_method(self, this, arguments):
        """
        ``Object.prototype.toLocaleString`` method implementation.

        15.2.4.3
        """
        o = self.interpreter.to_object(this)
        to_string = o.get('toString')
        if not is_callable(to_string):
            raise ESTypeError('toString is not a function')
        return to_string.call(o, [])

    def value_of_method(self, this, arguments):
        """
        ``Object.prototype.valueOf`` method implementation.

        15.2.4.4
        """
        return self.interpreter.to_object(this)

    def has_own_property_method(self, this, arguments):
        """
        ``Object.prototype.hasOwnProperty`` method implementation.

        15.2.4.5
        """
        v = get_arguments(arguments, count=1)
        p = self.interpreter.to_string(v)
        o = self.interpreter.to_object(this)
        desc = o.get_own_property(p)
        if desc is Undefined:
            return False
        return True

    def is_prototype_of_method(self, this, arguments):
        """
        ``Object.prototype.isPrototypeOf`` method implementation.

        15.2.4.6
        """
        v = get_arguments(arguments, count=1)
        if get_primitive_type(v) is not ObjectType:
            return False
        o = self.interpreter.to_object(this)
        v = v.prototype
        while o is not v:
            if v is None:
                return False
            v = v.prototype
        return True

    def property_is_enumerable_method(self, this, arguments):
        """
        ``Object.prototype.propertyIsEnumerable`` method implementation.

        15.2.4.7
        """
        v = get_arguments(arguments, count=1)
        p = self.interpreter.to_string(v)
        o = self.interpreter.to_object(this)
        desc = o.get_own_property(p)
        if desc is Undefined:
            return False
        return bool(desc.enumerable)
