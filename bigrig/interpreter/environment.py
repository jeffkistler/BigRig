"""
Specification types for resolving identifiers in execution contexts.
"""
from .types import (
    get_primitive_type, Undefined, ObjectType, NumberType, BooleanType, StringType
)
from .objects import PropertyDescriptor
from .exceptions import ESTypeError, ESReferenceError


class Binding(object):
    """
    A name binding in an execution context.
    """
    def __init__(self, value=None, can_delete=True, is_mutable=True):
        self.value = value
        self.can_delete = can_delete
        self.is_mutable = is_mutable


class EnvironmentRecord(object):
    """
    Associates names with bindings in an syntactic context.

    10.2.1
    """
    pass


class DeclarativeEnvironmentRecord(EnvironmentRecord):
    """
    Associates names with bindings in functions, variable declarations, catch 
    clauses, etc.

    10.2.1.1
    """
    def __init__(self):
        self.bindings = {}

    def has_binding(self, identifier):
        """
        10.2.1.1.1
        """
        return identifier in self.bindings

    def create_mutable_binding(self, identifier, can_delete=True):
        """
        10.2.1.1.2
        """
        binding = Binding(value=Undefined, can_delete=can_delete, is_mutable=True)
        self.bindings[identifier] = binding
        return binding

    def set_mutable_binding(self, identifier, value, strict=False):
        """
        10.2.1.1.3
        """
        binding = self.bindings[identifier]
        if binding.is_mutable:
            binding.value = value
        elif strict:
            raise ESTypeError('%s is immutable' % identifier)

    def get_binding_value(self, identifier, strict=False):
        """
        10.2.1.1.4
        """
        if identifier not in self.bindings and strict:
            raise ESReferenceError('%s is undefined' % identifier)
        binding = self.bindings.get(identifier)
        value = binding and binding.value
        if value is None and strict:
            raise ESReferenceError('%s is undefined' % identifier)
        elif value is None:
            return Undefined
        return value

    def delete_binding(self, identifier):
        """
        10.2.1.1.5
        """
        if identifier not in self.bindings:
            return True
        binding = self.bindings[identifier]
        if binding.can_delete:
            del self.bindings[identifier]
            return True
        return False

    def create_immutable_binding(self, identifier):
        """
        10.2.1.1.7
        """
        binding = Binding(value=None, can_delete=False, is_mutable=False)
        self.bindings[identifier] = binding
        return binding

    def initialize_immutable_binding(self, identifier, value):
        """
        10.2.1.1.8
        """
        binding = self.bindings[identifier]
        if binding.value is None:
            binding.value = value

    def implicit_this_value(self):
        """
        10.2.1.1.6
        """
        return Undefined


class ObjectEnvironmentRecord(EnvironmentRecord):
    """
    Associates names with bindings in a program, with statement, etc.

    10.2.1.2
    """
    def __init__(self, bindings, provide_this=False):
        # bindings here is an ObjectInstance
        self.bindings = bindings
        self.provide_this = provide_this

    def has_binding(self, identifier):
        """
        10.2.1.2.1
        """
        return self.bindings.has_property(identifier)

    def create_mutable_binding(self, identifier, can_delete=True):
        """
        10.2.1.2.2
        """
        if not self.bindings.has_property(identifier):
            configurable = can_delete
            desc = PropertyDescriptor(
                value=None, writable=True, enumerable=True, configurable=True
            )
            self.bindings.define_own_property(identifier, desc, True) # FIXME

    def set_mutable_binding(self, identifier, value, strict=False):
        """
        10.2.1.2.3
        """
        self.bindings.put(identifier, value, throw=strict)

    def get_binding_value(self, identifier, strict=False):
        """
        10.2.1.2.4
        """
        value = self.bindings.has_property(identifier)
        if not value and strict:
            raise ESReferenceError('%s is undefined' % identifier)
        elif not value:
            return Undefined
        return self.bindings.get(identifier)

    def delete_binding(self, identifier):
        """
        10.2.1.2.5
        """
        return self.bindings.delete(identifier, False)

    def implicit_this_value(self):
        """
        10.2.1.2.6
        """
        if self.provide_this:
            return self.bindings
        return Undefined


class LexicalEnvironment(object):
    """
    Specification type used to define the association of identifiers to
    specific values in a lexical scope.

    10.2
    """
    def __init__(self):
        self.outer = None
        self.environment_record = None

    def get_identifier_reference(self, identifier, strict=False):
        """
        10.2.2.1
        """
        if self.environment_record.has_binding(identifier):
            return Reference(self.environment_record, identifier, strict=strict)
        elif self.outer is not None:
            return self.outer.get_identifier_reference(identifier, strict=strict)
        elif self.outer is None:
            return Reference(Undefined, identifier, strict=strict)

    def new_declarative_environment(self, outer):
        """
        10.2.2.2
        """
        env = LexicalEnvironment()
        env.outer = outer
        env.environment_record = DeclarativeEnvironmentRecord()
        return env

    def new_object_environment(self, obj, outer):
        """
        10.2.2.3
        """
        env = LexicalEnvironment()
        env.environment_record = ObjectEnvironmentRecord(obj)
        env.outer = outer
        return env


class ExecutionContext(object):
    """
    Holds the active lexical bindings and active ``this`` value for the current
    position in the code execution stack.

    10.3
    """
    def __init__(self, lexical_environment, variable_environment, this_binding):
        self.lexical_environment = lexical_environment
        self.variable_environment = variable_environment
        self.this_binding = this_binding


class Reference(object):
    """
    Specification type used to resolve names to bindings.

    8.7
    """
    def __init__(self, base, name, strict=False):
        self.base = base
        self.name = name
        self.strict = strict

    def get_base(self):
        """
        Returns the base value component of this reference.
        """
        return self.base

    def get_referenced_name(self):
        """
        Returns the name component of this reference.
        """
        return self.name

    def is_strict_reference(self):
        """
        Returns the strict component of this reference.
        """
        return self.strict

    def has_primitive_base(self):
        """
        Returns whether the base component is a boolean, number or string.
        """
        if isinstance(self.base, ObjectType):
            return False
        primitive_type = get_primitive_type(self.base)
        return primitive_type in (BooleanType, NumberType, StringType)

    def is_property_reference(self):
        """
        Returns whether the base component is ``Object`` coercible.
        """
        return isinstance(self.base, ObjectType) or self.has_primitive_base()

    def is_unresolvable_reference(self):
        """
        Returns whether the base is undefined.
        """
        return self.base is Undefined
