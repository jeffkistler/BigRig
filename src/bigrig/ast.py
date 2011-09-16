"""
Abstract syntax tree node types.
"""
from bigrig.node import Node

#
# Statements
#

class Statement(Node):
    abstract = True

class BreakableStatement(Statement):
    abstract = True

class Block(BreakableStatement):
    abstract = False
    fields = ('statements',)

class IterationStatement(BreakableStatement):
    abstract = True

class DoWhileStatement(IterationStatement):
    abstract = False
    fields = ('condition', 'body')

class WhileStatement(IterationStatement):
    abstract = False
    fields = ('condition', 'body')

class ForStatement(IterationStatement):
    abstract = False
    fields = ('initialize', 'condition', 'next', 'body')

class ForInStatement(IterationStatement):
    abstract = False
    fields = ('each', 'enumerable', 'body')

class ExpressionStatement(Statement):
    abstract = False
    fields = ('expression',)

class LabelledStatement(Statement):
    abstract = False
    fields = ('label', 'statement')

class ContinueStatement(Statement):
    abstract = False
    fields = ('target',) # IterationStatement, is this supplied?

class BreakStatement(Statement):
    abstract = False
    fields = ('target',)

class ReturnStatement(Statement):
    abstract = False
    fields = ('expression',)

class CaseClause(BreakableStatement): #?
    abstract = False
    fields = ('label', 'statements')

class SwitchStatement(BreakableStatement):
    abstract = False
    fields = ('expression', 'cases')

class IfStatement(Statement):
    abstract = False
    fields = ('condition', 'then_statement', 'else_statement')

class TryStatement(Statement):
    abstract = False
    fields = ('try_block', 'catch_var', 'catch_block', 'finally_block')

class WithStatement(Statement):
    abstract = False
    fields = ('expression', 'statement')

class VariableDeclaration(Node):
    abstract = False
    fields = ('name', 'value')

class VariableStatement(Statement):
    abstract = False
    fields = ('declarations',)

class EmptyStatement(Statement):
    abstract = False

#
# Expressions
#

class Expression(Node):
    abstract = True

    def is_valid_left_hand_side(self):
        return False

class Name(Expression):
    abstract = False
    fields = ('value',)

    def is_valid_left_hand_side(self):
        return True

class NullNode(Expression):
    abstract = False

class TrueNode(Expression):
    abstract = False

class FalseNode(Expression):
    abstract = False

class ThisNode(Expression):
    abstract = False

class Literal(Expression):
    abstract = True

class StringLiteral(Literal):
    abstract = False
    fields = ('value',)

class NumberLiteral(Literal):
    abstract = False
    fields = ('value',)

class ObjectLiteral(Literal):
    abstract = False
    fields = ('properties',)

class ObjectProperty(Node):
    abstract = False
    fields = ('name', 'value')

class PropertyName(Node):
    abstract = False
    fields = ('value',)

class RegExpLiteral(Literal):
    abstract = False
    fields = ('pattern', 'flags',)

class ArrayLiteral(Literal):
    abstract = False
    fields = ('elements',)

#
# Operators
#

class PropertyAccess(Expression):
    abstract = True
    fields = ('object', 'key')

    def is_valid_left_hand_side(self):
        return True

class DotProperty(PropertyAccess):
    abstract = False

class BracketProperty(PropertyAccess):
    abstract = False

class CallExpression(Expression):
    abstract = False
    fields = ('expression', 'arguments')

class NewExpression(Expression):
    abstract = False
    fields = ('expression', 'arguments')

class UnaryOperation(Expression):
    abstract = False
    fields = ('op', 'expression')

class TypeofOperation(Expression):
    abstract = False
    fields = ('expression',)

class DeleteOperation(Expression):
    abstract = False
    fields = ('expression',)

class VoidOperation(Expression):
    abstract = False
    fields = ('expression',)

class PrefixCountOperation(Expression):
    abstract = False
    fields = ('op', 'expression')

class PostfixCountOperation(Expression):
    abstract = False
    fields = ('op', 'expression')

class BinaryOperation(Expression):
    abstract = False
    fields = ('op', 'left', 'right')

class CompareOperation(Expression):
    abstract = False
    fields = ('op', 'left', 'right')

class Conditional(Expression):
    abstract = False
    fields = ('condition', 'then_expression', 'else_expression')

class Assignment(Expression):
    abstract = False
    fields = ('op', 'target', 'value')

#
# Other stuff
#

class Throw(Expression):
    abstract = False
    fields = ('exception',)

class Function(Node):
    abstract = True
    fields = ('name', 'parameters', 'body')

class FunctionDeclaration(Function):
    abstract = False

class FunctionExpression(Function):
    abstract = False

class SourceElements(Expression):
    abstract = False
    fields = ('statements',)

