"""

"""
from itertools import izip_longest
import math
from ..parser.visitor import NodeVisitor
from ..parser.ast import Program, Function, ExpressionStatement, StringLiteral
from ..parser import ParseException
from .locator_parser import make_string_parser
from .exceptions import (
    ESError, ESTypeError, ESReferenceError, ESSyntaxError, ESReferenceError,
    ESRangeError, ESEvalError, ESURIError, WrappedError
)
from .environment import ExecutionContext, EnvironmentRecord, Reference
from .types import Conversions, Undefined, Null, NumberType, ObjectType, get_primitive_type
from .objects import PropertyDescriptor, is_accessor_descriptor, is_data_descriptor
from .objects.object import ObjectConstructor, ObjectPrototype
from .objects.function import (
    FunctionConstructor, FunctionPrototype, NativeFunctionInstance,
    ScriptFunctionInstance, EvalFunctionInstance
)
from .objects.arguments import Arguments
from .objects.array import ArrayConstructor, ArrayPrototype
from .objects.boolean import BooleanConstructor, BooleanPrototype
from .objects.date import DateConstructor, DatePrototype
from .objects.error import create_error
from .objects.global_obj import GlobalObject
from .objects.math import MathObject
from .objects.number import NumberConstructor, NumberPrototype
from .objects.regexp import RegExpConstructor, RegExpPrototype
from .objects.string import StringConstructor, StringPrototype
from .objects.console import ConsoleObject
from .visitor import EvaluationVisitor
from .environment import LexicalEnvironment, ExecutionContext, ObjectEnvironmentRecord
from .ast_utils import DeclarationVisitor
from .literals import IdentifierParser


class Interpreter(Conversions):
    """
    Object responsible for holding state and executing ECMAScript code.
    """
    def __init__(self):
        self.execution_contexts = []
        self.declarations = {}
        self.strict_contexts = []
        self.label_sets = {}
        self.declaration_visitor = DeclarationVisitor()
        self.evaluation_visitor = EvaluationVisitor(self)
        self.setup()

    def setup(self):
        """
        Construct the built-ins and initialize the execution context.
        """
        # Prototypes
        self.ObjectPrototype = ObjectPrototype(self)
        self.FunctionPrototype = FunctionPrototype(self)
        self.NumberPrototype = NumberPrototype(self)
        self.BooleanPrototype = BooleanPrototype(self)
        self.StringPrototype = StringPrototype(self)
        self.ArrayPrototype = ArrayPrototype(self)
        self.RegExpPrototype = RegExpPrototype(self)
        self.DatePrototype = DatePrototype(self)

        # Constructors
        self.ObjectConstructor = ObjectConstructor(self)
        self.ObjectPrototype.set_property('constructor', self.ObjectConstructor)
        self.ObjectConstructor.set_property('prototype', self.ObjectPrototype)

        self.FunctionConstructor = FunctionConstructor(self)
        self.FunctionPrototype.set_property('constructor', self.FunctionConstructor)
        self.FunctionConstructor.set_property('prototype', self.FunctionPrototype)

        self.NumberConstructor = NumberConstructor(self)
        self.NumberPrototype.set_property('constructor', self.NumberConstructor)
        self.NumberConstructor.set_property('prototype', self.NumberPrototype)

        self.BooleanConstructor = BooleanConstructor(self)
        self.BooleanPrototype.set_property('constructor', self.BooleanConstructor)
        self.BooleanConstructor.set_property('prototype', self.BooleanPrototype)

        self.StringConstructor = StringConstructor(self)
        self.StringPrototype.set_property('constructor', self.StringConstructor)
        self.StringConstructor.set_property('prototype', self.StringPrototype)

        self.ArrayConstructor = ArrayConstructor(self)
        self.ArrayPrototype.set_property('constructor', self.ArrayConstructor)
        self.ArrayConstructor.set_property('prototype', self.ArrayPrototype)

        self.RegExpConstructor = RegExpConstructor(self)
        self.RegExpPrototype.set_property('constructor', self.RegExpConstructor)
        self.RegExpConstructor.set_property('prototype', self.RegExpPrototype)

        self.DateConstructor = DateConstructor(self)
        self.DatePrototype.set_property('constructor', self.DateConstructor)
        self.DateConstructor.set_property('prototype', self.DatePrototype)

        self.ErrorConstructor = create_error(self, 'Error')
        self.EvalErrorConstructor = create_error(self, 'EvalError')
        self.RangeErrorConstructor = create_error(self, 'RangeError')
        self.ReferenceErrorConstructor = create_error(self, 'ReferenceError')
        self.SyntaxErrorConstructor = create_error(self, 'SyntaxError')
        self.TypeErrorConstructor = create_error(self, 'TypeError')
        self.URIErrorConstructor = create_error(self, 'URIError')

        self.Arguments = Arguments(self)
        self.Global = GlobalObject(self)
        self.Math = MathObject(self)
        self.Console = ConsoleObject(self)

        # Eval
        self.EvalFunctionInstance = EvalFunctionInstance(self)

        def raise_type_error(this, arguments):
            raise ESTypeError()
        self.ThrowTypeError = NativeFunctionInstance(self, raise_type_error)

        # Set up the global environment
        self.Global.set_property('Object', self.ObjectConstructor)
        self.Global.set_property('Function', self.FunctionConstructor)
        self.Global.set_property('Number', self.NumberConstructor)
        self.Global.set_property('Boolean', self.BooleanConstructor)
        self.Global.set_property('String', self.StringConstructor)
        self.Global.set_property('Array', self.ArrayConstructor)
        self.Global.set_property('RegExp', self.RegExpConstructor)
        self.Global.set_property('Date', self.DateConstructor)
        self.Global.set_property('Math', self.Math)
        self.Global.set_property('eval', self.EvalFunctionInstance)
        self.Global.set_property('console', self.Console)
        self.Global.set_property('Error', self.ErrorConstructor)
        self.Global.set_property('EvalError', self.EvalErrorConstructor)
        self.Global.set_property('RangeError', self.RangeErrorConstructor)
        self.Global.set_property('ReferenceError', self.ReferenceErrorConstructor)
        self.Global.set_property('SyntaxError', self.SyntaxErrorConstructor)
        self.Global.set_property('TypeError', self.TypeErrorConstructor)
        self.Global.set_property('URIError', self.URIErrorConstructor)

        # Initialize the execution context
        lexical_environment = LexicalEnvironment()
        lexical_environment.environment_record = ObjectEnvironmentRecord(self.Global)
        self.global_environment = ExecutionContext(
            lexical_environment, lexical_environment, self.Global
        )
        self.execution_contexts.append(self.global_environment)

    def enter_execution_context(self, lexical_environment, variable_environment, this_binding):
        context = ExecutionContext(lexical_environment, variable_environment, this_binding)
        self.execution_contexts.append(context)

    def leave_execution_context(self):
        self.execution_contexts.pop()

    def enter_strict_context(self, is_strict):
        self.strict_contexts.append(is_strict)

    def leave_strict_context(self):
        self.strict_contexts.pop()

    def in_strict_code(self):
        return self.strict_contexts[-1]

    @property
    def execution_context(self):
        assert self.execution_contexts
        return self.execution_contexts[-1]

    def exception_to_error(self, exception):
        if isinstance(exception, WrappedError):
            return exception.error
        elif isinstance(exception, ESTypeError):
            cons = self.TypeErrorConstructor
        elif isinstance(exception, ESSyntaxError):
            cons = self.SyntaxErrorConstructor
        elif isinstance(exception, ESReferenceError):
            cons = self.ReferenceErrorConstructor
        elif isinstance(exception, ESRangeError):
            cons = self.RangeErrorConstructor
        elif isinstance(exception, ESEvalError):
            cons = self.EvalErrorConstructor
        elif isinstance(exception, ESURIError):
            cons = self.URIErrorConstructor
        else:
            cons = self.ErrorConstructor
        return cons.construct([exception.message])

    def error_to_exception(self, error):
        return WrappedError(error)

    def create_function(self, declaration, scope, strict):
        # 13.2
        func = ScriptFunctionInstance(
            self, declaration, scope, strict
        )
        func.prototype = self.FunctionPrototype
        func.set_property('length', len(func.formal_parameters), False)
        prototype = self.ObjectConstructor.construct([])
        prototype.set_property('constructor', func, writable=True, configurable=True)
        func.set_property('prototype', prototype, writable=True)
        if strict:
            desc = PropertyDescriptor(
                get=self.ThrowTypeError, set=self.ThrowTypeError,
                enumerable=False, configurable=False
            )
            func.set_property('caller', desc, False)
            func.set_property('arguments', PropertyDescriptor.clone(desc), False)
        return func

    def visit_declarations(self, ast):
        declaration_map = self.declaration_visitor.get_node_scopes(ast)
        self.declarations.update(declaration_map)

    def make_string_parser(self, string, filename=None):
        return make_string_parser(string, filename=filename)

    def execute_statements(self, statements):
        return self.evaluation_visitor.visit_statement_list(statements)

    def execute_function(self, node):
        return self.execute_statements(node.body)

    def execute_program(self, program):
        self.visit_declarations(program)
        function_declarations, variable_declarations, strict = self.declarations[program]
        self.declaration_binding_instantiation(
            'global', function_declarations, variable_declarations, strict=strict
        )
        self.enter_strict_context(strict)
        try:
            completion_type, value, target = self.execute_statements(program.statements)
        finally:
            self.leave_strict_context()
        return value

    def execute_string(self, string, filename=None):
        try:
            program = self.make_string_parser(string, filename=filename).parse()
            return self.execute_program(program)
        except ParseException, e:
            return self.SyntaxErrorConstructor.construct([e.message])

    def declaration_binding_instantiation(self, declaration_binding_type,
                                          function_declarations, variable_declarations,
                                          function_instance=None, arguments=None, strict=False):
        # 10.5
        # 10.4.1 for global code
        # 10.4.2 for eval code
        # 10.4.3 for function code
        variable_env = self.execution_context.variable_environment
        env = variable_env.environment_record
        configurable_bindings = declaration_binding_type == 'eval'
        names = []
        # If we're in a function call, bind the passed arguments
        if declaration_binding_type == 'function':
            names = function_instance.formal_parameters
            for name, value in izip_longest(names, arguments, fillvalue=Undefined):
                if name is not Undefined:
                    name = IdentifierParser.parse_string(name)
                if not env.has_binding(name):
                    env.create_mutable_binding(name)
                    env.set_mutable_binding(name, value, strict=strict)
        # Step 5
        for function_declaration in function_declarations:
            function_name = IdentifierParser.parse_string(function_declaration.name)
            func = self.create_function(function_declaration, variable_env, strict)
            if not env.has_binding(function_name):
                env.create_mutable_binding(function_name, configurable_bindings)
            elif env is self.global_environment.lexical_environment.environment_record:
                existing_property = self.Global.get_property(function_name)
                if existing_property.configurable:
                    desc = PropertyDescriptor(
                        value=Undefined, writable=True, enumerable=True,
                        configurable=configurable_bindings
                    )
                    self.Global.define_own_property(function_name, desc, True)
                elif is_accessor_descriptor(existing_property) or not (existing_property.writable and existing_property.enumerable):
                    raise ESTypeError()
            env.set_mutable_binding(function_name, func, strict)
        # Step 6
        arguments_already_declared = env.has_binding('arguments')
        if not arguments_already_declared and declaration_binding_type == 'function':
            arguments_object = self.Arguments.create_arguments_object(
                function_instance, names, arguments, env, strict
            )
            if strict:
                env.create_immutable_binding('arguments')
                env.initialize_immutable_binding('arguments', arguments_object)
            else:
                env.create_mutable_binding('arguments')
                env.set_mutable_binding('arguments', arguments_object, strict=False)
        for variable_declaration in variable_declarations:
            variable_name = variable_declaration.name
            if not env.has_binding(variable_name):
                env.create_mutable_binding(variable_name, configurable_bindings)
                env.set_mutable_binding(variable_name, Undefined, strict=strict)

    def strict_equal(self, x, y):
        # 11.9.6
        to_primitive = self.to_primitive
        tx = get_primitive_type(x)
        ty = get_primitive_type(y)
        if tx != ty:
            return False
        elif tx is Undefined or tx is Null:
            return True
        elif tx is NumberType:
            x = to_primitive(x)
            y = to_primitive(y)
            if math.isnan(x) or math.isnan(y):
                return False
            return x == y
        elif tx is ObjectType:
            return x is y
        # StringType
        return x == y

    def get_value(self, value):
        # 8.7.1
        if not isinstance(value, Reference):
            return value
        else:
            name = value.get_referenced_name()
            if value.is_unresolvable_reference():
                raise ESReferenceError('%s is not defined' % name)
            base = value.get_base()
            if value.is_property_reference():
                if value.has_primitive_base():
                    base_object = self.to_object(base)
                    descriptor = base_object.get_property(name)
                    if descriptor is Undefined:
                        return descriptor
                    elif is_data_descriptor(descriptor):
                        return descriptor.value
                    elif is_accessor_descriptor(descriptor):
                        getter = descriptor.get
                        if getter is Undefined:
                            return Undefined
                        else:
                            getter.call(base, [])
                else:
                    return base.get(value.get_referenced_name())
            else:
                assert isinstance(base, EnvironmentRecord)
                return base.get_binding_value(name, value.is_strict_reference())

    def put_value(self, ref, value):
        # 8.7.2
        if not isinstance(ref, Reference):
            raise ESReferenceError('Invalid assignment')
        name = ref.get_referenced_name()
        base = ref.get_base()
        strict = ref.is_strict_reference()
        if ref.is_unresolvable_reference():
            if strict:
                raise ESReferenceError('Cannot resolve referenced name: %s' % name)
            self.Global.put(name, value, False)
        elif ref.is_property_reference():
            if ref.has_primitive_base():
                o = self.to_object(base)
                if not o.can_put(name):
                    if strict:
                        raise ESTypeError('%s is not writable in strict mode' % name)
                    return
                own_desc = o.get_own_property(name)
                if is_data_descriptor(own_desc):
                    if strict:
                        raise ESTypeError('%s is not writable in strict mode' % name)
                    return
                desc = o.get_property(name)
                if is_accessor_descriptor(desc):
                    setter = desc.set
                    setter.call(base, [value])
                elif strict:
                    raise ESTypeError('%s is not writable in strict mode' % name)
            else:
                base.put(name, value, strict)
        else:
            base.set_mutable_binding(name, value, strict)
