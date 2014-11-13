from bigrig.ast import *

class NodeFactory(object):
    """
    Encapsulates abstract syntax tree node creation.
    """

    def is_valid_left_hand_side(self, expression):
        return isinstance(expression, Node) and expression.is_valid_left_hand_side()

    #
    # Statements
    #

    def create_block(self, statements):
        return Block(statements)

    def create_do_while_statement(self, condition, body):
        return DoWhileStatement(condition, body)

    def create_while_statement(self, condition, body):
        return WhileStatement(condition, body)
    
    def create_for_statement(self, initializer, condition, next, body):
        return ForStatement(initializer, condition, next, body)

    def create_for_in_statement(self, each, enumerable, body):
        return ForInStatement(each, enumerable, body)

    def create_expression_statement(self, expression):
        return ExpressionStatement(expression)

    def create_labelled_statement(self, label, statement):
        return LabelledStatement(label, statement)

    def create_continue_statement(self, target):
        return ContinueStatement(target)

    def create_break_statement(self, target):
        return BreakStatement(target)

    def create_return_statement(self, expression):
        return ReturnStatement(expression)

    def create_case_clause(self, label, statements):
        return CaseClause(label, statements)

    def create_switch_statement(self, expression, cases):
        return SwitchStatement(expression, cases)

    def create_if_statement(self, condition, then_statement, else_statement):
        return IfStatement(condition, then_statement, else_statement)

    def create_try_statement(self, try_block, catch_var, catch_block, finally_block):
        return TryStatement(try_block, catch_var, catch_block, finally_block)

    def create_with_statement(self, expression, statement):
        return WithStatement(expression, statement)

    def create_variable_declaration(self, name, value):
        return VariableDeclaration(name, value)

    def create_variable_statement(self, declarations):
        return VariableStatement(declarations)

    def create_empty_statement(self):
        return EmptyStatement()

    #
    # Expressions
    #

    def create_null_node(self):
        return NullNode()

    def create_true_node(self):
        return TrueNode()

    def create_false_node(self):
        return FalseNode()

    def create_this_node(self):
        return ThisNode()

    def create_name(self, value):
        return Name(value)

    def create_string_literal(self, value):
        return StringLiteral(value)

    def create_number_literal(self, value):
        return NumberLiteral(value)

    def create_object_literal(self, properties):
        return ObjectLiteral(properties)

    def create_object_property(self, name, value):
        return ObjectProperty(name, value)

    def create_property_name(self, value):
        return PropertyName(value)

    def create_property_getter(self, name, body):
        return PropertyGetter(name, body)

    def create_property_setter(self, name, parameter, body):
        return PropertySetter(name, parameter, body)

    def create_regexp_literal(self, pattern, flags):
        return RegExpLiteral(pattern, flags)

    def create_array_literal(self, elements):
        return ArrayLiteral(elements)

    def create_elision(self):
        return Elision()

    def create_dot_property(self, object, key):
        return DotProperty(object, key)

    def create_bracket_property(self, object, key):
        return BracketProperty(object, key)

    def create_call_expression(self, expression, arguments):
        return CallExpression(expression, arguments)

    def create_new_expression(self, expression, arguments):
        return NewExpression(expression, arguments)

    def create_unary_operation(self, op, expression):
        return UnaryOperation(op, expression)

    def create_typeof_operation(self, expression):
        return TypeofOperation(expression)

    def create_delete_operation(self, expression):
        return DeleteOperation(expression)

    def create_void_operation(self, expression):
        return VoidOperation(expression)

    def create_prefix_count_operation(self, op, expression):
        return PrefixCountOperation(op, expression)

    def create_postfix_count_operation(self, op, expression):
        return PostfixCountOperation(op, expression)

    def create_binary_operation(self, op, left, right):
        return BinaryOperation(op, left, right)

    def create_compare_operation(self, op, left, right):
        return CompareOperation(op, left, right)

    def create_conditional(self, condition, then_expression, else_expression):
        return Conditional(condition, then_expression, else_expression)

    def create_assignment(self, op, target, value):
        return Assignment(op, target, value)

    def create_throw(self, exception):
        return Throw(exception)

    def create_function_declaration(self, name, parameters, body):
        return FunctionDeclaration(name, parameters, body)

    def create_function_expression(self, name, parameters, body):
        return FunctionExpression(name, parameters, body)

    def create_parameters(self, parameters):
        return parameters

    def create_source_elements(self, statements):
        return SourceElements(statements)

    def create_program(self, statements):
        return Program(statements)
    
        
