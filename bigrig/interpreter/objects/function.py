"""
Specialized instance classes and the constructor for Function specification
objects.
"""
from bigrig.parser.ast import FunctionExpression
from bigrig.parser import ParseException
from . import is_callable, PropertyDescriptor
from .base import FunctionInstance, ObjectInstance
from ..types import (
    Undefined, Null, ObjectType, StringType,
    get_arguments, get_primitive_type, is_primitive
)
from ..exceptions import ESError, ESTypeError, ESSyntaxError
from ..ast_utils import code_is_strict


class ScriptFunctionInstance(FunctionInstance):
    """
    A specialized class for script-defined functions.
    """
    def __init__(self, interpreter, node, scope, strict):
        super(ScriptFunctionInstance, self).__init__(interpreter)
        self.node = node
        self.scope = scope
        self.formal_parameters = node.parameters or []
        self.code = node.body or []
        self.strict = strict
        self.set_property('length', len(self.formal_parameters))

    def call(self, this, arguments):
        """
        13.2.1
        """
        func = self.node
        interpreter = self.interpreter
        function_declarations, variable_declarations, strict = interpreter.declarations[func]
        # 10.4.3
        if strict:
            this_binding = this
        elif this is Undefined or this is Null:
            this_binding = interpreter.Global
        elif is_primitive(this):
            this_binding = interpreter.to_object(this)
        else:
            this_binding = this
        outer_env = interpreter.execution_context.lexical_environment
        local_env = outer_env.new_declarative_environment(self.scope)
        interpreter.enter_execution_context(local_env, local_env, this_binding)
        interpreter.enter_strict_context(strict)
        try:
            interpreter.declaration_binding_instantiation(
                'function', function_declarations, variable_declarations,
                function_instance=self, arguments=arguments, strict=strict
            )
            completion_type, value, target = interpreter.execute_function(func)
        finally:
            interpreter.leave_execution_context()
            interpreter.leave_strict_context()
        if completion_type == 'throw':
            raise interpreter.error_to_exception(value)
        elif completion_type == 'return':
            return value
        return Undefined

    def construct(self, arguments):
        """
        13.2.2
        """
        obj = ObjectInstance(self.interpreter)
        obj.extensible = True
        prototype = self.get('prototype')
        if get_primitive_type(prototype) != ObjectType:
            prototype = self.interpreter.ObjectPrototype
        obj.prototype = prototype
        result = self.call(obj, arguments)
        if get_primitive_type(result) == ObjectType:
            return result
        return obj


class BoundFunctionInstance(FunctionInstance):
    """
    A specialized class for functions returned by ``Function.prototype.bind``.
    """
    def __init__(self, interpreter, target_function, bound_args, bound_this):
        super(BoundFunctionInstance, self).__init__(interpreter)
        self.target_function = target_function
        self.bound_args = bound_args
        self.bound_this = bound_this

    def call(self, this, arguments):
        """
        15.3.4.5.1
        """
        args = self.bound_args + arguments
        return self.target_function.call(self.bound_this, args)

    def construct(self, arguments):
        """
        15.3.4.5.2
        """
        target = self.target_function
        if not (hasattr(target, 'construct') and callable(target.construct)):
            raise ESTypeError('Invalid constructor')
        args = self.bound_args + arguments
        return target.construct(args)

    def has_instance(self, value):
        """
        15.3.4.5.3
        """
        target = self.target_function
        if not (hasattr(target, 'has_instance') and  callable(target.has_instance)):
            raise ESTypeError('Invalid function')
        return target.has_instance(value)


class NativeFunctionInstance(FunctionInstance):
    """
    A specialized class for functions whose implementation is in Python code.
    """
    def __init__(self, interpreter, native, length=0, name=None):
        super(NativeFunctionInstance, self).__init__(interpreter)
        self.name = name
        self.native = native
        self.set_property('length', length)

    @property
    def prototype(self):
        return self.interpreter.FunctionPrototype

    def call(self, this, arguments):
        return self.native(this, arguments)


def define_native_method(obj, name, method, length=0,
                         writable=True, enumerable=False, configurable=True):
    """
    Define a property for an instance method corresponding to a native implementation.
    """
    func = NativeFunctionInstance(obj.interpreter, method, length=length, name=name)
    obj.set_property(
        name, func, writable=writable, enumerable=enumerable, configurable=configurable
    )


class EvalFunctionInstance(FunctionInstance):
    """
    A specialized class for the ``eval`` built-in function.
    """
    def __init__(self, interpreter):
        super(EvalFunctionInstance, self).__init__(interpreter)
        self.set_property('length', 1)
        self.prototype = interpreter.FunctionPrototype

    def call(self, this, arguments, direct=False):
        """
        15.1.2.1
        """
        x = arguments and arguments[0] or Undefined
        if get_primitive_type(x) is not StringType:
            return x
        code = self.interpreter.to_string(x)
        try:
            prog = self.interpreter.make_string_parser(code.encode('utf-8')).parse()
        except ParseException, e:
            raise ESSyntaxError(e.message)
        # 10.4.2
        interpreter = self.interpreter
        if not direct:
            context = interpreter.global_environment
            this = interpreter.Global
        else:
            context = interpreter.execution_context
        lexical_env = context.lexical_environment
        variable_env = context.variable_environment
        interpreter.visit_declarations(prog)
        function_declarations, variable_declarations, strict = interpreter.declarations[prog]
        if strict:
            lexical_env = lexical_env.new_declarative_environment(lexical_env)
            variable_env = lexical_env
        interpreter.enter_execution_context(
            lexical_env, variable_env, this
        )
        interpreter.enter_strict_context(strict)
        try:
            self.interpreter.visit_declarations(prog)
            interpreter.declaration_binding_instantiation(
                'eval', function_declarations, variable_declarations, strict=strict
            )
            completion_type, value, target = interpreter.execute_statements(
                prog.statements
            )
        except ESError, e:
            completion_type = 'throw'
            value = interpreter.exception_to_error(e)
        finally:
            interpreter.leave_execution_context()
            interpreter.leave_strict_context()
        if completion_type == 'normal' and value is not None:
            return value
        elif completion_type == 'throw':
            raise interpreter.error_to_exception(value)
        return Undefined


class FunctionConstructor(FunctionInstance):
    """
    The ``Function`` constructor function.

    15.3.1 & 15.3.2
    """
    def __init__(self, interpreter):
        super(FunctionConstructor, self).__init__(interpreter)
        self.prototype = interpreter.FunctionPrototype
        self.set_property('length', 1)

    def call(self, this, arguments):
        """
        15.3.1.1
        """
        return self.construct(arguments)

    def construct(self, arguments):
        """
        15.3.2.1
        """
        parameter_list = []
        num_args = len(arguments)
        if num_args == 0:
            body = ''
        else:
            parameter_list = arguments[:-1]
            body = arguments[-1]
        body = self.interpreter.to_string(body)
        if parameter_list:
            try:
                parameters = u'%s)' % u','.join(self.interpreter.to_string(param) for param in parameter_list)
                parameters = parameters.encode('utf-8')
                parser = self.interpreter.make_string_parser(parameters)
                parameter_list = parser.parse_parameter_list()
            except ParseException, e:
                raise ESSyntaxError(e.message)
        try:
            body = body.encode('utf-8')
            parser = self.interpreter.make_string_parser(body)
            body = parser.parse_source_elements()
        except ParseException, e:
            raise ESSyntaxError(e.message)
        strict = code_is_strict(body)
        declaration = FunctionExpression()
        declaration.parameters = parameter_list
        declaration.body = body
        # Make sure this function and its children  get added to the
        # node to declarations map
        self.interpreter.visit_declarations(declaration)
        execution_context = self.interpreter.global_environment
        outer_env = execution_context.lexical_environment
        scope = outer_env.new_declarative_environment(outer_env)
        func = self.interpreter.create_function(declaration, scope, strict)
        return func


class FunctionPrototype(FunctionInstance):
    """
    The prototype object assigned to ``Function`` instances.

    15.3.4
    """
    def __init__(self, interpreter):
        super(FunctionPrototype, self).__init__(interpreter)
        self.prototype = interpreter.ObjectPrototype
        self.set_property('length', 0)
        define_native_method(self, 'toString', self.to_string_method)
        define_native_method(self, 'apply', self.apply_method, 2)
        define_native_method(self, 'call', self.call_method, 1)
        define_native_method(self, 'bind', self.bind_method, 1)

    def call(self, this, arguments):
        """
        15.3.4
        """
        return Undefined

    def get_function_info(self, func):
        """
        """
        name = u''
        parameters = u''
        code = u'[native code]'
        if isinstance(func, ScriptFunctionInstance):
            if func.node.name is not None:
                name = func.node.name
            parameters = u', '.join(func.formal_parameters)
            code = u'[script code]'
        elif isinstance(func, BoundFunctionInstance):
            return self.get_function_info(func.target_function)
        elif isinstance(func, NativeFunctionInstance):
            if func.name is not None:
                name = func.name
        elif isinstance(func, EvalFunctionInstance):
            name = u'eval'
        return name, parameters, code

    def to_string_method(self, this, arguments):
        """
        ``Function.prototype.toString`` method implementation.

        15.3.4.2
        """
        if not is_callable(this):
            raise ESTypeError('Function.prototype.toString is not generic')
        name, parameters, code = self.get_function_info(this)
        return u'function %s(%s) { %s }' % (name, parameters, code)

    def apply_method(self, this, arguments):
        """
        ``Function.prototype.apply`` method implementation.

        15.3.4.3
        """
        if not is_callable(this):
            raise ESTypeError('Function.prototype.apply called on a non-function')
        this_arg, arg_array = get_arguments(arguments, count=2)
        if arg_array is Undefined or arg_array is Null:
            return this.call(this_arg, [])
        if get_primitive_type(arg_array) is not ObjectType:
            raise ESTypeError('Function.prototype.apply arguments list is not an object')
        length = arg_array.get('length')
        n = self.interpreter.to_uint32(length)
        arg_list = []
        for i in range(n):
            arg_list.append(arg_array.get(unicode(i)))
        return this.call(this_arg, arg_list)

    def call_method(self, this, arguments):
        """
        ``Function.prototype.call`` method implementation.

        15.3.4.4
        """
        if not is_callable(this):
            raise ESTypeError('Function.prototype.call called on a non-function')
        this_arg = get_arguments(arguments, count=1)
        arg_list = arguments[1:]
        return this.call(this_arg, arg_list)

    def bind_method(self, this, arguments):
        """
        ``Function.prototype.bind`` method implementation.

        15.3.4.5
        """
        target = this
        if not is_callable(this):
            raise ESTypeError('Function.prototype.bind called on a non-function')
        this_arg = get_arguments(arguments, count=1)
        arg_list = arguments[1:]
        f = BoundFunctionInstance(
            self.interpreter, target, arg_list, this_arg
        )
        f.prototype = self.interpreter.FunctionPrototype
        f.extensible = True
        length = 0
        if target.es_class == 'Function':
            length = target.get('length') - len(arg_list)
            length = max(length, 0)
        f.set_property('length', length)
        thrower = self.interpreter.ThrowTypeError
        desc = PropertyDescriptor(
            get=thrower, set=thrower, enumerable=False, configurable=False
        )
        f.define_own_property('caller', desc, False)
        f.define_own_property('arguments', PropertyDescriptor.clone(desc), False)
        return f
