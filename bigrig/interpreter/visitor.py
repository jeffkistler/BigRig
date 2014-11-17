"""
Abstract syntax tree visitor that performs evaluation on the nodes.
"""
import math
from ..parser import ast
from ..parser.visitor import NodeVisitor
from .types import (
    Undefined, Null, NumberType, StringType, ObjectType, BooleanType,
    get_primitive_type, check_object_coercible, NaN
)
from .exceptions import ESError, ESTypeError, ESSyntaxError
from .environment import Reference, EnvironmentRecord
from .objects import PropertyDescriptor, is_callable, is_data_descriptor, is_accessor_descriptor
from .objects.base import FunctionInstance, ObjectInstance
from .literals import IdentifierParser, StringLiteralParser, NumberLiteralParser
from .ast_utils import code_is_strict


class EvaluationVisitor(NodeVisitor):
    """
    Abstract syntax tree evaluator.
    """
    def __init__(self, interpreter):
        self.interpreter = interpreter
        super(EvaluationVisitor, self).__init__()

    def check_valid_ref(self, ref):
        if isinstance(ref, Reference) and ref.is_strict_reference():
            if isinstance(ref.get_base(), EnvironmentRecord):
                name = ref.get_referenced_name()
                if name in ('eval', 'arguments'):
                    raise ESTypeError('Cannot assign to %s in strict mode' % name)

    def get_qualified_name(self, ref):
        # FIXME
        if isinstance(ref, Reference):
            return ref.get_referenced_name()
        return ''

    def get_value(self, ref):
        return self.interpreter.get_value(ref)

    def put_value(self, ref, value):
        return self.interpreter.put_value(ref, value)

    # Expressions

    def visit_Name(self, node):
        # 11.1.2
        # 10.3.1
        name = IdentifierParser.parse_string(node.value)
        execution_context = self.interpreter.execution_context
        env = execution_context.lexical_environment
        strict = self.interpreter.in_strict_code()
        return env.get_identifier_reference(name, strict=strict)

    def visit_ThisNode(self, node):
        # 11.1.1
        execution_context = self.interpreter.execution_context
        return execution_context.this_binding

    def visit_NullNode(self, node):
        return Null

    def visit_TrueNode(self, node):
        # 7.8
        return True

    def visit_FalseNode(self, node):
        # 7.8
        return False

    def visit_NumberLiteral(self, node):
        # 7.8
        value = node.value
        strict = self.interpreter.in_strict_code()
        return NumberLiteralParser.parse_string(value, allow_octal=not strict)

    def visit_StringLiteral(self, node):
        # 7.8
        strict = self.interpreter.in_strict_code()
        return StringLiteralParser.parse_string(node.value, allow_octal=not strict)

    def visit_ArrayLiteral(self, node):
        # 11.1.4
        array = self.interpreter.ArrayConstructor.construct([])
        length = len(node.elements)
        for i, element in enumerate(node.elements):
            if not isinstance(element, ast.Elision):
                init_result = self.visit(element)
                init_value = self.get_value(init_result)
                desc = PropertyDescriptor(
                    value=init_value, writable=True, enumerable=True, configurable=True
                )
                array.define_own_property(unicode(i), desc, False)
        array.put('length', self.interpreter.to_uint32(length))
        return array

    def visit_RegExpLiteral(self, node):
        # Strip the ``/``s here
        pattern = node.pattern[1:-1]
        return self.interpreter.RegExpConstructor.construct([pattern, node.flags])

    def visit_PropertyName(self, node):
        return IdentifierParser.parse_string(node.value)

    def visit_ObjectProperty(self, node):
        name = self.visit(node.name)
        name = self.interpreter.to_string(name)
        expr_value = self.visit(node.value)
        prop_value = self.get_value(expr_value)
        descriptor = PropertyDescriptor(
            value=prop_value, writable=True, enumerable=True, configurable=True
        )
        return (name, descriptor)

    def visit_PropertyGetter(self, node):
        name = node.name
        strict = self.interpreter.in_strict_code() or code_is_strict(node.body)
        declaration = ast.FunctionExpression()
        declaration.body = node.body
        # Make sure this function and its children  get added to the
        # node to declarations map
        self.interpreter.visit_declarations(declaration)
        execution_context = self.interpreter.execution_context
        outer_env = execution_context.lexical_environment
        scope = outer_env.new_declarative_environment(outer_env)
        func = self.interpreter.create_function(declaration, scope, strict)
        descriptor = PropertyDescriptor(
            get=func, enumerable=True, configurable=True
        )
        return (name, descriptor)

    def visit_PropertySetter(self, node):
        name = node.name
        strict = self.interpreter.in_strict_code() or code_is_strict(node.body)
        declaration = ast.FunctionExpression()
        declaration.parameters = [node.parameter]
        declaration.body = node.body
        # Make sure this function and its children  get added to the
        # node to declarations map
        self.interpreter.visit_declarations(declaration)
        execution_context = self.interpreter.execution_context
        outer_env = execution_context.lexical_environment
        scope = outer_env.new_declarative_environment(outer_env)
        func = self.interpreter.create_function(declaration, scope, strict)
        descriptor = PropertyDescriptor(
            set=func, enumerable=True, configurable=True
        )
        return (name, descriptor)

    def visit_ObjectLiteral(self, node):
        # 11.1.5
        new_obj = self.interpreter.ObjectConstructor.construct([])
        strict = self.interpreter.in_strict_code()
        for prop in node.properties:
            (name, descriptor) = self.visit(prop)
            previous = new_obj.get_own_property(name)
            if previous is not Undefined:
                if strict and is_data_descriptor(previous) and is_data_descriptor(descriptor):
                    raise ESSyntaxError(
                        'Duplicate data property in object literal not allowed in strict mode'
                    )
                elif is_data_descriptor(previous) and is_accessor_descriptor(descriptor):
                    raise ESSyntaxError()
                elif is_accessor_descriptor(previous) and is_data_descriptor(descriptor):
                    raise ESSyntaxError()
                elif is_accessor_descriptor(previous) and is_accessor_descriptor(descriptor):
                    if previous.get is not None and descriptor.get is not None:
                        raise ESSyntaxError()
                    elif previous.set is not None and descriptor.set is not None:
                        raise ESSyntaxError()
            new_obj.define_own_property(name, descriptor, False)
        return new_obj

    def visit_DotProperty(self, node):
        # 11.2.1
        base_reference = self.visit(node.object)
        base_value = self.get_value(base_reference)
        property_name_reference = node.key
        property_name_value = self.get_value(property_name_reference)
        check_object_coercible(base_value)
        property_name_string = self.interpreter.to_string(property_name_value)
        strict = self.interpreter.in_strict_code()
        return Reference(base_value, property_name_string, strict=strict)

    def visit_BracketProperty(self, node):
        # 11.2.1
        base_reference = self.visit(node.object)
        base_value = self.get_value(base_reference)
        property_name_reference = self.visit(node.key)
        property_name_value = self.get_value(property_name_reference)
        check_object_coercible(base_value)
        property_name_string = self.interpreter.to_string(property_name_value)
        strict = self.interpreter.in_strict_code()
        return Reference(base_value, property_name_string, strict=strict)

    def visit_CallExpression(self, node):
        reference = self.visit(node.expression)
        function = self.get_value(reference)
        arguments = [self.get_value(self.visit(argument)) for argument in node.arguments]
        if not isinstance(function, FunctionInstance) or not is_callable(function):
            name = self.get_qualified_name(reference)
            raise ESTypeError('%s is not a function' % name)
        is_reference = isinstance(reference, Reference)
        if is_reference:
            if reference.is_property_reference():
                this = reference.get_base()
            else:
                base = reference.get_base()
                this = base.implicit_this_value()
        else:
            this = Undefined
        # Check if is direct call to eval, 15.1.2.1.1
        if is_reference and reference.name == 'eval' and function == self.interpreter.EvalFunctionInstance:
            return function.call(this, arguments, direct=True)
        return function.call(this, arguments)

    def visit_NewExpression(self, node):
        # 11.2.2
        reference = self.visit(node.expression)
        constructor = self.get_value(reference)
        if get_primitive_type(constructor) is not ObjectType:
            name = self.get_qualified_name(reference)
            raise ESTypeError('%s is not a constructor' % name)
        if not hasattr(constructor, 'construct') or not callable(constructor.construct):
            name = self.get_qualified_name(reference)
            raise ESTypeError('%s is not a constructor' % name)
        if node.arguments:
            arguments = [self.get_value(self.visit(argument)) for argument in node.arguments]
        else:
            arguments = []
        return constructor.construct(arguments)

    def visit_FunctionExpression(self, node):
        execution_context = self.interpreter.execution_context
        lexical_environment = execution_context.lexical_environment
        func_env = lexical_environment.new_declarative_environment(
            lexical_environment
        )
        if node.name:
            env_record = func_env.environment_record
            env_record.create_immutable_binding(node.name)
        strict = self.interpreter.in_strict_code()
        obj = self.interpreter.create_function(node, func_env, strict)
        if node.name:
            env_record.initialize_immutable_binding(node.name, obj)
        return obj

    def visit_UnaryOperation(self, node):
        expr = self.visit(node.expression)
        op = node.op
        # op must be in +, -, ~, !
        if op == '+':
            return self.interpreter.to_number(self.get_value(expr))
        elif op == '-':
            old_value = self.interpreter.to_number(self.get_value(expr))
            if math.isnan(old_value):
                return NaN
            return -old_value
        elif op == '~':
            old_value = self.interpreter.to_int32(self.get_value(expr))
            return ~old_value
        elif op == '!':
            old_value = self.interpreter.to_boolean(self.get_value(expr))
            return not old_value

    def visit_TypeofOperation(self, node):
        val = self.visit(node.expression)
        if isinstance(val, Reference):
            if val.is_unresolvable_reference():
                return "undefined"
            val = self.get_value(val)
        primitive_type = get_primitive_type(val)
        if primitive_type is Undefined:
            return "undefined"
        elif primitive_type is Null:
            return "null"
        elif primitive_type is BooleanType:
            return "boolean"
        elif primitive_type is NumberType:
            return "number"
        elif primitive_type is StringType:
            return "string"
        elif primitive_type is ObjectType and isinstance(val, FunctionInstance):
            return "function"
        elif primitive_type is ObjectType:
            return "object"

    def visit_DeleteOperation(self, node):
        reference = self.visit(node.expression)
        if not isinstance(reference, Reference):
            return True
        if reference.is_unresolvable_reference():
            if reference.is_strict_reference():
                raise ESSyntaxError('Cannot delete an unqualified identifier in strict mode.')
            else:
                return True
        elif reference.is_property_reference():
            base_object = self.interpreter.to_object(reference.get_base())
            return base_object.delete(
                reference.get_referenced_name(), reference.is_strict_reference()
            )
        if reference.is_strict_reference():
            raise ESSyntaxError('Cannot delete an unqualified identifier in strict mode.')
        bindings = reference.get_base()
        return bindings.delete_binding(reference.get_referenced_name())

    def visit_VoidOperation(self, node):
        expression = self.visit(node.expression)
        self.get_value(expression)
        return Undefined

    def invalid_ref(self, ref):
        if isinstance(ref, Reference) and ref.is_strict_reference():
            if isinstance(ref.get_base(), EnvironmentRecord):
                name = ref.get_referenced_name()
                if name in ('eval', 'arguments'):
                    raise ESSyntaxError('Cannot assign to %s in strict mode')

    def visit_PrefixCountOperation(self, node):
        # 11.4.4 & 11.4.5
        expr = self.visit(node.expression)
        self.check_valid_ref(expr)
        old_value = self.interpreter.to_number(self.get_value(expr))
        if node.op == '++':
            new_value = old_value + 1
        else:
            new_value = old_value - 1
        self.put_value(expr, new_value)
        return new_value

    def visit_PostfixCountOperation(self, node):
        # 11.3
        lhs = self.visit(node.expression)
        self.check_valid_ref(lhs)
        old_value = self.interpreter.to_number(self.get_value(lhs))
        if node.op == '++':
            new_value = old_value + 1
        else:
            new_value = old_value - 1
        self.put_value(lhs, new_value)
        return old_value

    def apply_binary_operator(self, op, lval, rval):
        # 11.5
        to_primitive = self.interpreter.to_primitive
        to_number = self.interpreter.to_number
        to_string = self.interpreter.to_string
        to_boolean = self.interpreter.to_boolean
        to_int32 = self.interpreter.to_int32
        to_uint32 = self.interpreter.to_uint32
        if op == '*':
            # 11.5.1
            left_num = to_number(lval)
            right_num = to_number(rval)
            return left_num * right_num
        elif op == '/':
            # 11.5.2
            left_num = to_number(lval)
            right_num = to_number(rval)
            if right_num == 0:
                return NaN
            return left_num / right_num
        elif op == '%':
            # 11.5.3
            left_num = to_number(lval)
            right_num = to_number(rval)
            if right_num == 0:
                return NaN
            return left_num % right_num
        elif op == '+':
            # 11.6.1
            lval = to_primitive(lval)
            rval = to_primitive(rval)
            if get_primitive_type(lval) is StringType or get_primitive_type(rval) is StringType:
                return to_string(lval) + to_string(rval)
            return to_number(lval) + to_number(rval)
        elif op == '-':
            # 11.6.2
            left_num = to_number(lval)
            right_num = to_number(rval)
            return left_num - right_num
        elif op == '<<':
            # 11.7.1
            left_num = to_int32(lval)
            right_num = to_uint32(rval)
            shift_count = right_num & 0x1F
            return left_num << shift_count
        elif op == '>>':
            # FIXME: should this wrap?
            # 11.7.2
            left_num = to_int32(lval)
            right_num = to_uint32(rval)
            shift_count = right_num & 0x1F
            return right_num >> shift_count
        elif op == '>>>':
            # 11.7.3
            left_num = to_uint32(lval)
            right_num = to_uint32(rval)
            shift_count = right_num & 0x1F
            return left_num >> right_num
        elif op == '&':
            left_num = to_int32(lval)
            right_num = to_int32(rval)
            return left_num & right_num
        elif op == '^':
            left_num = to_int32(lval)
            right_num = to_int32(rval)
            return left_num ^ right_num
        elif op == '|':
            left_num = to_int32(lval)
            right_num = to_int32(rval)
            return left_num | right_num
        elif op == ',':
            return rval

    def visit_BinaryOperation(self, node):
        left = self.visit(node.left)
        lval = self.get_value(left)
        if node.op == '&&':
            if not self.interpreter.to_boolean(lval):
                return lval
            right = self.visit(node.right)
            rval = self.get_value(right)
            return rval
        elif node.op == '||':
            if self.interpreter.to_boolean(lval):
                return lval
            right = self.visit(node.right)
            rval = self.get_value(right)
            return rval
        else:
            right = self.visit(node.right)
            rval = self.get_value(right)
        return self.apply_binary_operator(node.op, lval, rval)

    def compare(self, x, y, left_first=True):
        # 11.8.5
        to_primitive = self.interpreter.to_primitive
        if not left_first:
            x, y = y, x
        px = to_primitive(x, preferred_type='Number')
        py = to_primitive(y, preferred_type='Number')
        if get_primitive_type(px) is StringType and get_primitive_type(py) is StringType:
            if px.startswith(py):
                return False
            elif py.startswith(px):
                return True
            return px < py
        else:
            to_number = self.interpreter.to_number
            nx = to_number(px)
            ny = to_number(py)
            if math.isnan(nx) or math.isnan(ny):
                return Undefined
            return nx < ny

    def equal(self, x, y):
        # 11.9.3
        to_number = self.interpreter.to_number
        to_string = self.interpreter.to_string
        to_boolean = self.interpreter.to_boolean
        to_primitive = self.interpreter.to_primitive

        tx = get_primitive_type(x)
        ty = get_primitive_type(y)
        x = to_primitive(x)
        y = to_primitive(y)
        if tx == ty:
            if tx is Undefined or tx is Null:
                return True
            if tx is ObjectType:
                return x is y
            return x == y
        elif x is Null and y is Undefined:
            return True
        elif tx is NumberType and ty is StringType:
            return x == to_number(y)
        elif tx is StringType and ty is NumberType:
            return to_number(x) == y
        elif tx is BooleanType:
            return to_number(x) == y
        elif ty is BooleanType:
            return x == to_number(y)
        # TODO: is this accurate?
        elif tx in (StringType, NumberType) and ty is ObjectType:
            return x == y
        elif tx is ObjectType and ty in (StringType, NumberType):
            return x == y
        return False
    
    def visit_CompareOperation(self, node):
        lref = self.visit(node.left)
        rref = self.visit(node.right)
        lval = self.get_value(lref)
        rval = self.get_value(rref)
        op = node.op
        if op == 'instanceof':
            if get_primitive_type(rval) is not ObjectType or not hasattr(rval, 'has_instance'):
                raise ESTypeError("Non-function operand for 'instanceof' check")
            return rval.has_instance(lval)
        elif op == 'in':
            if get_primitive_type(rval) is not ObjectType:
                raise ESTypeError("Non-object operand for 'in'")
            lname = self.interpreter.to_string(lval)
            return rval.has_property(lname)
        elif op == '<':
            r = self.compare(lval, rval)
            if r is Undefined:
                return False
            return r
        elif op == '>':
            r = self.compare(lval, rval, left_first=False)
            if r is Undefined:
                return False
            return r
        elif op == '<=':
            r = self.compare(lval, rval, left_first=False)
            if r is True or r is Undefined:
                return False
            return True
        elif op == '>=':
            r = self.compare(lval, rval)
            if r is True or r is Undefined:
                return False
            return True
        elif op == '==':
            # 11.9.1
            return self.equal(rval, lval)
        elif op == '!=':
            return not self.equal(rval, lval)
        elif op == '===':
            return self.interpreter.strict_equal(lval, rval)
        elif op == '!==':
            return not self.interpreter.strict_equal(lval, rval)

    def visit_Conditional(self, node):
        lref = self.visit(node.condition)
        if self.interpreter.to_boolean(self.get_value(lref)):
            ref = self.visit(node.then_expression)
        else:
            ref = self.visit(node.else_expression)
        return self.get_value(ref)

    def visit_Assignment(self, node):
        lref = self.visit(node.target)
        self.check_valid_ref(lref)
        rref = self.visit(node.value)
        rval = self.get_value(rref)
        if node.op == '=':
            self.put_value(lref, rval)
            return rval
        else:
            lval = self.get_value(lref)
            op = node.op[:-1]
            r = self.apply_binary_operator(op, lval, rval)
            self.put_value(lref, r)
            return r

    # Statements

    def visit_statement_list(self, statements):
        completion_type = 'normal'
        value = None
        target = None
        for statement in statements:
            try:
                (completion_type, s_value, target) = self.visit(statement)
            except ESError, e:
                completion_type = 'throw'
                s_value = self.interpreter.exception_to_error(e)
                target = None
            if completion_type != 'normal':
                return (completion_type, s_value, target)
            if s_value is not None:
                value = s_value
        return (completion_type, value, target)

    def visit_Block(self, node):
        return self.visit_statement_list(node.statements)

    def visit_DoWhileStatement(self, node):
        label_set = self.interpreter.label_sets.get(node, set())
        v = None
        iterating = True
        while iterating:
            (comp_type, value, target) = stmt = self.visit(node.body)
            if value is not None:
                v = value
            if comp_type is not 'continue' or (target is not None and target not in label_set):
                if comp_type == 'break' and (target is None or target in label_set):
                    return ('normal', v, None)
                elif comp_type != 'normal':
                    return stmt
            expr_ref = self.visit(node.condition)
            if not self.interpreter.to_boolean(self.get_value(expr_ref)):
                iterating = False
        return ('normal', v, None)

    def visit_WhileStatement(self, node):
        label_set = self.interpreter.label_sets.get(node, set())
        v = None
        expression_boolean = lambda res: self.interpreter.to_boolean(self.get_value(res))
        while expression_boolean(self.visit(node.condition)):
            (comp_type, value, target) = stmt = self.visit(node.body)
            if value is not None:
                v = value
            if comp_type != 'continue' or (target is not None and target not in label_set):
                if comp_type == 'break' and (target is None or target in label_set):
                    return ('normal', v, None)
                if comp_type != 'normal':
                    return stmt
        return ('normal', v, None)

    def visit_ForStatement(self, node):
        label_set = self.interpreter.label_sets.get(node, set())
        if node.initialize:
            expr_ref = self.visit(node.initialize)
            self.get_value(expr_ref)
        v = None
        test_expr = node.condition
        inc_expr = node.next
        while True:
            if test_expr:
                test_expr_ref = self.visit(test_expr)
                if not self.interpreter.to_boolean(self.get_value(test_expr_ref)):
                    return ('normal', v, None)
            (comp_type, value, target) = stmt = self.visit(node.body)
            if value is not None:
                v = value
            if comp_type == 'break' and (target is None or target in label_set):
                return ('normal', v, None)
            if comp_type != 'continue' or (target is not None and target not in label_set):
                if comp_type != 'normal':
                    return stmt
            if inc_expr:
                inc_expr_ref = self.visit(inc_expr)
                self.get_value(inc_expr_ref)
        return ('normal', v, None)

    def visit_ForInStatement(self, node):
        label_set = self.interpreter.label_sets.get(node, set())
        expr_ref = self.visit(node.enumerable)
        expr_val = self.get_value(expr_ref)
        if expr_val is Null or expr_val is Undefined:
            return ('normal', None, None)
        obj = self.interpreter.to_object(expr_val)
        v = None
        seen = set()
        current = obj
        while current is not None:
            keys = current.properties.keys()
            for key in keys:
                if key in seen or key not in current.properties:
                    continue
                desc = current.properties[key]
                if not desc.enumerable:
                    continue
                seen.add(key)
                lhs_ref = self.visit(node.each)
                self.put_value(lhs_ref, key)
                (comp_type, value, target) = stmt = self.visit(node.body)
                if value is not None:
                    v = value
                if comp_type == 'break' and (target is None or target in label_set):
                    return ('normal', v, None)
                if comp_type != 'continue' or (target is not None and target not in label_set):
                    if comp_type != 'normal':
                        return stmt
            current = getattr(current, 'prototype', None)
        return ('normal', v, None)

    def visit_ExpressionStatement(self, node):
        expr_ref = self.visit(node.expression)
        return ('normal', self.get_value(expr_ref), None)

    def visit_LabelledStatement(self, node):
        label = node.label.value
        node_labels = set((label,))
        label_sets = self.interpreter.label_sets
        if node in label_sets:
            node_labels.update(label_sets[node])
        label_sets[node.statement] = node_labels
        comp_type, value, target = self.visit(node.statement)
        if comp_type == 'break' and target == label:
            return ('normal', value, None)
        return (comp_type, value, target)

    def visit_ContinueStatement(self, node):
        target = None
        if node.target is not None:
            target = self.visit(node.target)
        return ('continue', None, target)

    def visit_BreakStatement(self, node):
        target = None
        if node.target is not None:
            target = self.visit(node.target)
        return ('break', None, target)

    def visit_ReturnStatement(self, node):
        value = None
        if node.expression is not None:
            expr_ref = self.visit(node.expression)
            value = self.get_value(expr_ref)
        return ('return', value, None)

    def visit_SwitchStatement(self, node):
        expr_ref = self.visit(node.expression)
        expr_val = self.get_value(expr_ref)
        v = None
        searching = True
        default = None
        for clause in node.cases:
            if clause.label is not None:
                clause_selector = self.get_value(self.visit(clause.label))
                if self.interpreter.strict_equal(clause_selector, expr_val):
                    searching = False
                    if clause.statements:
                        comp_type, value, target = result = self.visit_statement_list(clause.statements)
                        if value is not None:
                            v = value
                        if comp_type != 'normal':
                            return (comp_type, v, target)
            else:
                default = clause
        if searching and default is not None:
            comp_type, v, target = self.visit_statement_list(default.statements)
        return ('normal', v, None)

    def visit_IfStatement(self, node):
        expr_ref = self.visit(node.condition)
        condition = self.interpreter.to_boolean(self.get_value(expr_ref))
        if condition:
            return self.visit(node.then_statement)
        elif node.else_statement:
            return self.visit(node.else_statement)
        return ('normal', None, None)

    def visit_Throw(self, node):
        expr_ref = self.visit(node.exception)
        return ('throw', self.get_value(expr_ref), None)

    def visit_TryStatement(self, node):
        try:
            (comp_type, value, target) = result = self.visit(node.try_block)
        except ESError, e:
            value = self.interpreter.exception_to_error(e)
            (comp_type, value, target) = result = ('throw', value, None)
        if comp_type == 'throw':
            if node.catch_var:
                identifier = node.catch_var.value
                execution_context = self.interpreter.execution_context
                old_env = execution_context.lexical_environment
                catch_env = old_env.new_declarative_environment(old_env)
                env = catch_env.environment_record
                env.create_mutable_binding(identifier)
                env.set_mutable_binding(identifier, value, False)
                execution_context.lexical_environment = catch_env
                try:
                    result = self.visit(node.catch_block)
                finally:
                    execution_context.lexical_environment = old_env
        if node.finally_block:
            (comp_type, value, target) = stmt = self.visit(node.finally_block)
            if comp_type != 'normal':
                return stmt
        return result

    def visit_WithStatement(self, node):
        strict = self.interpreter.in_strict_code()
        if strict:
            error = self.interpreter.SyntaxErrorConstructor.construct([
                'The with statement is not allowed in strict mode code'
            ])
            return ('throw', error, None)
        val = self.visit(node.expression)
        obj = self.interpreter.to_object(self.get_value(val))
        old_env = self.interpreter.execution_context.lexical_environment
        new_env = old_env.new_object_environment(obj, old_env)
        new_env.provide_this = True
        self.interpreter.execution_context.lexical_environment = new_env
        try:
            stmt = self.visit(node.statement)
        except ESError, e:
            stmt = ('throw', e, None)
        finally:
            self.interpreter.execution_context.lexical_environment = old_env
        return stmt

    def get_reference(self, name):
        env = self.interpreter.execution_context.lexical_environment
        strict = self.interpreter.in_strict_code()
        return env.get_identifier_reference(name, strict=strict)

    def visit_VariableDeclaration(self, node):
        lhs = self.get_reference(node.name)
        self.check_valid_ref(lhs)
        if node.value:
            rhs = self.visit(node.value)
            value = self.get_value(rhs)
            self.put_value(lhs, value)
        strict = self.interpreter.in_strict_code()
        return lhs

    def visit_VariableStatement(self, node):
        self.visit(node.declarations)
        return ('normal', None, None)

    def visit_EmptyStatement(self, node):
        return ('normal', None, None)

    def visit_FunctionDeclaration(self, node):
        return ('normal', None, None)

    def visit_Program(self, node):
        return self.visit_statement_list(node.statements)
