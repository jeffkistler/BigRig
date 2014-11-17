"""
The ``Arguments`` specification object.
"""
from ..types import Undefined
from ..exceptions import ESTypeError
from . import PropertyDescriptor, is_accessor_descriptor
from .base import ObjectInstance
from .function import NativeFunctionInstance, FunctionInstance


class Arguments(ObjectInstance):
    """
    The specialized object assigned to the ``arguments`` local in the
    declaration binding process.

    10.6
    """
    def __init__(self, interpreter):
        super(Arguments, self).__init__(interpreter)
        self.strict = False
        self.parameter_map = None

    def create_arguments_object(self, func, names, args, env, strict):
        """
        Build and return the ``arguments`` and assign it all required
        properties.
        """
        args_length = len(args)
        names_length = len(names)
        obj = Arguments(self.interpreter)
        obj.es_class = 'Arguments'
        obj.prototype = self.interpreter.ObjectPrototype
        obj.strict = strict
        length_descriptor = PropertyDescriptor(
            value=args_length, writable=True, enumerable=False, configurable=True
        )
        obj.define_own_property('length', length_descriptor, False)
        arguments_map = self.interpreter.ObjectConstructor.construct([])
        mapped_names = []
        for indx, val in zip(range(args_length - 1, -1, -1), reversed(args)):
            arg_desc = PropertyDescriptor(
                value=val, writable=True, enumerable=True, configurable=True
            )
            obj.define_own_property(unicode(indx), arg_desc, False)
            if indx < names_length:
                name = names[indx]
                if not strict and name not in mapped_names:
                    mapped_names.append(name)
                    getter = lambda this, arguments: env.get_binding_value(name)
                    setter = lambda this, arguments: env.set_mutable_binding(name, arguments and arguments[0] or Undefined)
                    g = NativeFunctionInstance(self.interpreter, getter)
                    p = NativeFunctionInstance(self.interpreter, setter)
                    name_desc = PropertyDescriptor(
                        get=g, set=p, configurable=True
                    )
                    arguments_map.define_own_property(name, name_desc, False)
        if mapped_names:
            obj.parameter_map = arguments_map
        if not strict:
            desc = PropertyDescriptor(
                value=func, writable=True, enumerable=False, configurable=True
            )
            obj.define_own_property('callee', desc, False)
        else:
            thrower = self.interpreter.ThrowTypeError
            desc = PropertyDescriptor(
                get=thrower, set=thrower, enumerable=False, configurable=False
            )
            obj.define_own_property('caller', desc, False)
            obj.define_own_property('callee', desc, False)
        return obj

    def get(self, name):
        """
        Specialized ``Get`` internal method.
        """
        if not self.strict and self.parameter_map:
            is_mapped = self.parameter_map.get_own_property(name)
            if is_mapped is Undefined:
                v = super(Arguments, self).get(name)
                if name == 'caller' and isinstance(v, FunctionInstance) and getattr(v, 'strict', False):
                    raise ESTypeError("'caller' is not accessible in strict mode")
            else:
                return self.parameter_map.get(name)
        return super(Arguments, self).get(name)

    def get_own_property(self, name):
        """
        Specialized ``GetOwnProperty`` internal method.
        """
        if not self.strict and self.parameter_map:
            desc = super(Arguments, self).get_own_property(name)
            if desc is Undefined:
                return desc
            is_mapped = self.parameter_map.get_own_property(name)
            if is_mapped is not Undefined:
                desc.value = self.parameter_map.get(name)
            return desc
        return super(Arguments, self).get_own_property(name)

    def define_own_property(self, name, descriptor, throw=False):
        """
        Specialized ``DefineOwnProperty`` internal method.
        """
        if not self.strict and self.parameter_map:
            is_mapped = self.parameter_map.get_own_property(name)
            allowed = super(Arguments, self).define_own_property(name, descriptor, False)
            if not allowed:
                if throw:
                    raise ESTypeError('Invalid property assignment')
                return False
            if is_mapped is not Undefined:
                if is_accessor_property(descriptor):
                    self.parameter_map.delete(name, False)
                else:
                    if descriptor.value is not None:
                        self.parameter_map.put(name, descriptor.value, throw)
                    if descriptor.writable is not None and descriptor.value is False:
                        self.parameter_map.delete(name, False)
            return True
        return super(Arguments, self).define_own_property(name, descriptor, throw)

    def delete(self, name, throw=False):
        """
        Specialized ``Delete`` internal method.
        """
        if not self.strict and self.parameter_map:
            is_mapped = self.parameter_map.get_own_property(name)
            result = super(Arguments, self).delete(name, throw)
            if result is True and is_mapped is not Undefined:
                self.parameter_map.delete(name, False)
            return result
        return super(Arguments, self).delete(name, throw)
