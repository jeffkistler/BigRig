from ..parser.ast import ExpressionStatement, StringLiteral
from ..parser.visitor import NodeVisitor


def code_is_strict(code):
    # 14.1
    if not code:
        return False
    strict = False
    for node in code:
        if not isinstance(node, ExpressionStatement):
            break
        elif not isinstance(node.expression, StringLiteral):
            break
        if node.expression.value[1:-1] == 'use strict':
            strict = True
            break
    return strict


class DeclarationVisitor(NodeVisitor):
    def __init__(self):
        super(DeclarationVisitor, self).__init__()
        self.scope_stack = None
        self.node_scopes = None

    def is_strict(self, code):
        return self.current_scope_is_strict() or code_is_strict(code)

    def enter_scope(self, strict=False):
        new_scope = ([], [], strict)
        self.scope_stack.append(new_scope)

    def leave_scope(self):
        return self.scope_stack.pop()

    def current_function_declaration_scope(self):
        return self.scope_stack[-1][0]

    def current_variable_declaration_scope(self):
        return self.scope_stack[-1][1]

    def current_scope_is_strict(self):
        return bool(self.scope_stack) and self.scope_stack[-1][2]

    def visit_VariableDeclaration(self, node):
        scope = self.current_variable_declaration_scope()
        scope.append(node)
        self.visit(node.value)

    def visit_FunctionDeclaration(self, node):
        strict = self.is_strict(node.body)
        scope = self.current_function_declaration_scope()
        scope.append(node)
        self.enter_scope(strict)
        self.visit(node.body)
        function_scope = self.leave_scope()
        self.node_scopes[node] = function_scope

    def visit_FunctionExpression(self, node):
        strict = self.is_strict(node.body)
        self.enter_scope(strict)
        self.visit(node.body)
        function_scope = self.leave_scope()
        self.node_scopes[node] = function_scope

    def visit_Program(self, node):
        strict = self.is_strict(node.statements)
        self.enter_scope(strict)
        self.visit(node.statements)
        program_scope = self.leave_scope()
        self.node_scopes[node] = program_scope

    def get_node_scopes(self, node):
        self.scope_stack = []
        self.node_scopes = {}
        self.visit(node)
        return self.node_scopes
