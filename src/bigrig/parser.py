"""
An ECMAScript 3 parser implementation and various related utilities.
"""
from bigrig.token import *
from bigrig.factory import NodeFactory

class ParseException(Exception):
    """
    Base exception for all parse errors.
    """
    pass

class BaseParser(object):
    """
    This class provides an ECMAScript 3rd Edition parser but no AST creation
    """
    def __init__(self, token_stream=None):
        self.token_stream = token_stream
        self.precedence_table = PRECEDENCE # From token
        self.accept_in = True

    #
    # Token utilities
    #

    def next(self):
        """
        Advance the scanner to the next token.
        """
        return self.token_stream.next()

    def peek(self):
        """
        Get the next token type without advancing the scanner.
        """
        return self.token_stream.peek().type

    def raise_unexpected_token(self, token, expected=None):
        """
        Raise a ``ParseException`` for an unexpected token.
        """
        message_template = "Unexpected token '%(token_value)s' on line %(line)d, column %(column)d."
        locator = token.locator
        format_args = {
            'token_type': token.type,
            'token_value': token.value,
            'filename': locator.filename,
            'line': locator.line,
            'column': locator.column
        }
        message = message_template % format_args
        if expected:
            message = message + " Expected '%s'." % expected
        raise ParseException(message)

    def expect(self, expected):
        """
        Ensure the next token is the expected type.
        """
        next = self.next()
        if next.type != expected:
            self.raise_unexpected_token(next, expected)
        return next

    def has_line_terminator_before_next(self):
        """
        Determine if the token stream has a line terminator before the next
        token in the stream. Useful for automatic semicolon insertion.
        """
        return self.token_stream.has_line_terminator_before_next

    def expect_semicolon(self):
        """
        Handle automatic semicolon insertion here.
        """
        next = self.peek()
        if next in (RIGHT_CURLY_BRACE, EOF):
            return Token(SEMICOLON, u';')
        elif self.has_line_terminator_before_next():
            return Token(SEMICOLON, u';')
        return self.expect(SEMICOLON)

    def scan_regexp(self):
        """
        Regular expression literal scanning is parse-context dependent, so we
        provide a way for the parser to make it happen.
        """
        return self.token_stream.scan_regexp()
    
    def scan_regexp_flags(self):
        """
        Make sure a REGEXP is followed by identifier parts for flags.
        """
        return self.token_stream.scan_regexp_flags()

    #
    # Operator utilities
    #

    def precedence(self, token):
        if not self.accept_in and token == IN:
            return 0
        return self.precedence_table.get(token, 0)

    def is_unary_op(self, token):
        return token in UNARY_OPS

    def is_comparison_op(self, token):
        return token in COMPARISON_OPS

    def is_assignment_op(self, token):
        return token in ASSIGNMENT_OPS

    def is_count_op(self, token):
        return token in COUNT_OPS

    #
    # Literals
    #

    def parse_object_literal(self):
        """
        ObjectLiteral ::
          '{' (
            ((Identifier | String | Number) ':' AssignmentExpression))*[',']
          '}'
        """
        self.expect(LEFT_CURLY_BRACE)
        properties = []
        while self.peek() != RIGHT_CURLY_BRACE:
            # Parse the key
            next = self.next()
            type = next.type
            if type == IDENTIFIER:
                name = self.create_property_name(next.value)
            elif type == STRING:
                name = self.create_string_literal(next.value)
            elif type in (DECIMAL, INTEGER):
                name = self.create_number_literal(next.value)
            else:
                raise self.raise_unexpected_token(next)
            self.expect(COLON)
            # Parse the value
            value = self.parse_assignment_expression()
            if self.peek() != RIGHT_CURLY_BRACE:
                self.expect(COMMA)
            properties.append(self.create_object_property(name, value))
        self.expect(RIGHT_CURLY_BRACE)
        return self.create_object_literal(properties)

    def parse_array_literal(self):
        """
        ArrayLiteral ::
          '[' Expression? (',' Expression?)* ']'
        """
        values = []
        self.expect(LEFT_BRACKET)
        while self.peek() != RIGHT_BRACKET:
            element = self.parse_assignment_expression()
            values.append(element)
            if self.peek() != RIGHT_BRACKET:
                self.expect(COMMA)
        self.expect(RIGHT_BRACKET)
        return self.create_array_literal(values)

    def parse_regexp_literal(self): # seen_equal?
        """
        RegularExpressionLiteral ::
          '/' RegularExpressionBody '/' RegularExpressionFlags
        """
        pattern = self.scan_regexp()
        if pattern.type != REGEXP:
            raise ParseException("Invalid regexp pattern")
        flags = self.scan_regexp_flags()
        if flags.type != IDENTIFIER:
            raise ParseException("Invalid regexp flags")
        return self.create_regexp_literal(pattern.value, flags.value)

    #
    # Expressions
    #

    def parse_expression(self):
        """
        Expression ::
          AssignmentExpression
          Expression ',' AssignmentExpression
        """
        result = self.parse_assignment_expression()
        while self.peek() == COMMA:
            comma = self.expect(COMMA)
            right = self.parse_assignment_expression()
            result = self.create_binary_operation(comma.value, result, right)
        return result

    def parse_primary_expression(self):
        """
        PrimaryExpression ::
          'this'
          'null'
          'true'
          'false'
          Identifier
          Number
          StringLiteral
          ArrayLiteral
          ObjectLiteral
          RegExpLiteral
          '(' Expression ')'
        """
        # Consider a dict here
        type = self.peek()
        if type == THIS:
            self.next()
            result = self.create_this_node()
        elif type == NULL:
            self.next()
            result = self.create_null_node()
        elif type == TRUE:
            self.next()
            result = self.create_true_node()
        elif type == FALSE:
            self.next()
            result = self.create_false_node()
        elif type == IDENTIFIER:
            next = self.next()
            result = self.create_name(next.value)
        elif type in (DECIMAL, INTEGER):
            next = self.next()
            result = self.create_number_literal(next.value)
        elif type == STRING:
            next = self.next()
            result = self.create_string_literal(next.value)
        elif type == LEFT_BRACKET:
            result = self.parse_array_literal()
        elif type == LEFT_CURLY_BRACE:
            result = self.parse_object_literal()
        elif type in (DIV, ASSIGN_DIV):
            result = self.parse_regexp_literal()
        elif type == LEFT_PAREN:
            self.expect(LEFT_PAREN)
            previous = self.accept_in
            self.accept_in = True
            result = self.parse_expression()
            self.accept_in = previous
            self.expect(RIGHT_PAREN)
        else:
            self.raise_unexpected_token(self.next())
        return result

    def parse_arguments(self):
        """
        Arguments ::
          '(' (AssignmentExpression)*[','] ')'
        """
        self.expect(LEFT_PAREN)
        result = []
        while self.peek() != RIGHT_PAREN:
            result.append(self.parse_assignment_expression())
            if self.peek() != RIGHT_PAREN:
                self.expect(COMMA)
        self.expect(RIGHT_PAREN)
        return result

    def parse_member_expression(self, allow_call=True):
        """
        MemberExpression ::
          PrimaryExpression
          FunctionExpression
          MemberExpression '[' Expression ']'
          MemberExpression '.' Identifier
          'new' MemberExpression Arguments
        """
        type = self.peek()
        if type == NEW:
            self.expect(NEW)
            expression = self.parse_member_expression(False)
            arguments = self.parse_arguments()
            result = self.create_new_expression(expression, arguments)
        elif type == FUNCTION:
            result = self.parse_function_expression()
        else:
            result = self.parse_primary_expression()
        return self.parse_member_expression_tail(allow_call, result)

    def parse_member_expression_tail(self, allow_call, node):
        """
        ( '(' Arguments ')' | '[' Expression ']' | '.' Expression ) *
        """
        type = self.peek()
        if type == DOT:
            self.expect(DOT)
            key = self.expect(IDENTIFIER)
            node = self.create_dot_property(node, key.value)
        elif type == LEFT_BRACKET:
            self.expect(LEFT_BRACKET)
            index = self.parse_expression()
            node = self.create_bracket_property(node, index)
            self.expect(RIGHT_BRACKET)
        elif type == LEFT_PAREN and allow_call:
            arguments = self.parse_arguments()
            node = self.create_call_expression(node, arguments)
        else:
            return node
        return self.parse_member_expression_tail(allow_call, node)

    def parse_left_hand_side_expression(self):
        """
        MemberExpression parsing handles these two productions.

        LeftHandSideExpression ::
          NewExpression
          CallExpression
        """
        return self.parse_member_expression()

    def parse_postfix_expression(self):
        """
        PostfixExpression ::
          LeftHandSideExpression ('++' | '--')?
        """
        expression = self.parse_left_hand_side_expression()
        if not self.has_line_terminator_before_next() and \
                self.is_count_op(self.peek()):
            op = self.next()
            return self.create_postfix_count_operation(op.value, expression)
        return expression

    def parse_unary_expression(self):
        """
        UnaryExpression ::
          PostfixExpression
          'delete' UnaryExpression
          'void' UnaryExpression
          'typeof' UnaryExpression
          '++' UnaryExpression
          '--' UnaryExpression
          '+' UnaryExpression
          '-' UnaryExpression
          '~' UnaryExpression
          '!' UnaryExpression
        """
        type = self.peek()
        if self.is_count_op(type):
            op = self.next()
            expression = self.parse_unary_expression()
            return self.create_prefix_count_operation(op.value, expression)
        elif self.is_unary_op(type):
            op = self.next()
            expression = self.parse_unary_expression()
            if type == TYPEOF:
                return self.create_typeof_operation(expression)
            elif type == DELETE:
                return self.create_delete_operation(expression)
            elif type == VOID:
                return self.create_void_operation(expression)
            return self.create_unary_operation(op.value, expression)
        return self.parse_postfix_expression()

    def parse_binary_operator_expression(self, lhs, min_precedence=4):
        """
        Parse an infix operator expression.
        
        See http://en.wikipedia.org/wiki/Operator-precedence_parser
        """
        while self.precedence(self.peek()) >= min_precedence:
            op = self.next()
            precedence = self.precedence(op.type)
            rhs = self.parse_unary_expression()
            next_precedence = self.precedence(self.peek())
            while next_precedence >= precedence:
                rhs = self.parse_binary_operator_expression(
                    rhs, next_precedence
                )
                next_precedence = self.precedence(self.peek())
            if self.is_comparison_op(op.type):
                lhs = self.create_compare_operation(
                    op.value, lhs, rhs
                )
            else:
                lhs = self.create_binary_operation(
                    op.value, lhs, rhs
                )
        return lhs

    def parse_assignment_expression(self):
        """
        AssignmentExpression ::
          ConditionalExpression
          LeftHandSideExpression AssignmentOperator AssignmentExpression
        """
        expression = self.parse_conditional_expression()
        if not self.is_assignment_op(self.peek()):
            return expression

        if expression is None or not self.is_valid_left_hand_side(expression):
            raise ParseException('Invalid assignment')
        
        op = self.next()
        right = self.parse_assignment_expression()

        return self.create_assignment(op.value, expression, right)

    def parse_conditional_expression(self):
        """
        ConditionalExpression ::
          LogicalOrExpression
          LogicalOrExpression '?' AssignmentExpression ':' AssignmentExpression
        """
        expression = self.parse_binary_operator_expression(self.parse_unary_expression())
        if self.peek() != HOOK:
            return expression
        self.expect(HOOK)
        left = self.parse_assignment_expression()
        self.expect(COLON)
        right = self.parse_assignment_expression()
        return self.create_conditional(expression, left, right)

    #
    # Statements
    #

    def parse_statement(self):
        """
        Statement ::
          Block
          VariableStatement
          EmptyStatement
          ExpressionStatement
          IfStatement
          IterationStatement
          ContinueStatement
          BreakStatement
          ReturnStatement
          WithStatement
          LabelledStatement
          SwitchStatement
          ThrowStatement
          TryStatement
        """
        # Consider a dict here
        type = self.peek()
        if type == LEFT_CURLY_BRACE:
            statement = self.parse_block_statement()
        elif type == VAR:
            statement = self.parse_variable_statement()
        elif type == SEMICOLON:
            statement = self.parse_empty_statement()
        elif type == IF:
            statement = self.parse_if_statement()
        elif type == DO:
            statement = self.parse_do_while_statement()
        elif type == WHILE:
            statement = self.parse_while_statement()
        elif type == FOR:
            statement = self.parse_for_statement()
        elif type == CONTINUE:
            statement = self.parse_continue_statement()
        elif type == BREAK:
            statement = self.parse_break_statement()
        elif type == RETURN:
            statement = self.parse_return_statement()
        elif type == WITH:
            statement = self.parse_with_statement()
        elif type == SWITCH:
            statement = self.parse_switch_statement()
        elif type == THROW:
            statement = self.parse_throw_statement()
        elif type == TRY:
            statement = self.parse_try_statement()
        else:
            statement = self.parse_expression_statement()
        return statement

    def parse_block_statement(self):
        """
        Block ::
          '{' Statement* '}'

        Does not introduce a new execution scope.
        """
        self.expect(LEFT_CURLY_BRACE)
        statements = []
        while self.peek() != RIGHT_CURLY_BRACE:
            statements.append(self.parse_statement())
        self.expect(RIGHT_CURLY_BRACE)
        return self.create_block(statements)

    def parse_variable_statement(self):
        """
        VariableStatement ::
          VariableDeclarations ';'
        """
        declarations = self.parse_variable_declarations()
        self.expect_semicolon()
        return self.create_variable_statement(declarations)

    def parse_variable_declarations(self):
        """
        VariableDeclarations ::
          'var' (Identifier (= AssignmentExpression)?)+[',']
        """
        self.expect(VAR)
        declarations = []
        while True:
            identifier = self.expect(IDENTIFIER)
            initializer = None
            if self.peek() == ASSIGN:
                self.expect(ASSIGN)
                initializer = self.parse_assignment_expression()
            declaration = self.create_variable_declaration(
                identifier.value, initializer
            )
            declarations.append(declaration)
            if self.peek() != COMMA:
                break
            self.expect(COMMA)
        return declarations

    def parse_empty_statement(self):
        """
        EmptyStatement ::
          ';'
        """
        self.expect(SEMICOLON)
        return self.create_empty_statement()

    def parse_expression_statement(self):
        """
        ExpressionStatement ::
          Expression ';'
        """
        expression = self.parse_expression()
        # Do this only if  expression is a name?
        if self.peek() == COLON:
            statement = self.parse_labelled_statement()
            return self.create_labelled_statement(expression, statement)
        self.expect_semicolon()
        return self.create_expression_statement(expression)

    def parse_labelled_statement(self):
        """
        LabelledStatement ::
          Identifier ':' Statement
        """
        self.expect(COLON)
        statement = self.parse_statement()
        return statement

    def parse_if_statement(self):
        """
        IfStatement ::
          'if' '(' Expression ')' Statement ('else' Statement)?
        """
        self.expect(IF)
        self.expect(LEFT_PAREN)
        condition = self.parse_expression()
        self.expect(RIGHT_PAREN)
        then_statement = self.parse_statement()
        if self.peek() == ELSE:
            self.expect(ELSE)
            else_statement = self.parse_statement()
        else:
            else_statement = None
        return self.create_if_statement(
            condition, then_statement, else_statement
        )

    def parse_do_while_statement(self):
        """
        DoStatement ::
          'do' Statement 'while' '(' Expression ')' ';'
        """
        self.expect(DO)
        body = self.parse_statement()
        self.expect(WHILE)
        self.expect(LEFT_PAREN)
        condition = self.parse_expression()
        self.expect(RIGHT_PAREN)
        if self.peek() == SEMICOLON:
            self.expect(SEMICOLON)
        return self.create_do_while_statement(condition, body)

    def parse_while_statement(self):
        """
        WhileStatement ::
          'while' '(' Expression ')' Statement
        """
        self.expect(WHILE)
        self.expect(LEFT_PAREN)
        expression = self.parse_expression()
        self.expect(RIGHT_PAREN)
        body = self.parse_statement()
        return self.create_while_statement(expression, body)

    def parse_for_statement(self):
        """
        ForStatement ::
          'for' '(' Expression? ';' Expression? ';' Expression? ')' Statement
          'for' '(' LeftHandSideExpression 'in' Expression ')' Statement


          'for' '(' ExpressionNoIn? ';' Expression? ';' Expression? ')' Statement
          'for' '(' 'var' VariableDeclarationListNoIn ';' Expression? ';' Expression? ')' Statement
          'for' '(' LeftHandSideExpression 'in' Expression ')' Statement
          'for' '(' 'var' VariableDeclarationNoIn 'in' Expression ')' Statement
        """
        self.accept_in = False
        self.expect(FOR)
        self.expect(LEFT_PAREN)
        initializer = None
        # Parse the initializer or possibly return a ForInStatement
        if self.peek() != SEMICOLON:
            if self.peek() == VAR:
                # If this is a single declaration, then allow 'in'
                variable_declarations = self.parse_variable_declarations()
                variable_statement = self.create_variable_statement(variable_declarations)
                if self.peek() == IN:
                    self.expect(IN)
                    enumerable = self.parse_expression()
                    self.expect(RIGHT_PAREN)
                    self.accept_in = True
                    body = self.parse_statement()
                    return self.create_for_in_statement(variable_statement, enumerable, body)
                else:
                    initializer = variable_statement
            else:
                expression = self.parse_expression()
                if self.peek() == IN:
                    if not expression.is_valid_left_hand_side():
                        # TODO: Better error reporting here.
                        raise ParseException(
                            'Invalid assignment in initializer.'
                        )
                    self.expect(IN)
                    enumerable = self.parse_expression()
                    self.expect(RIGHT_PAREN)
                    self.accept_in = True
                    body = self.parse_statement()
                    return self.create_for_in_statement(
                        expression, enumerable, body
                    )
                else:
                    initializer = expression
        # TODO: Better error reporting here.
        # if self.peek() != SEMICOLON:
        #     self.raise("Invalid initializer expression in for statement")
        # Parse the rest of the ForStatement
        self.expect(SEMICOLON)
        self.accept_in = True
        condition = None
        if self.peek() != SEMICOLON:
            condition = self.parse_expression()
        self.expect(SEMICOLON)
        next = None
        if self.peek() != RIGHT_PAREN:
            next = self.parse_expression()
        self.expect(RIGHT_PAREN)
        self.accept_in = True
        body = self.parse_statement()
        return self.create_for_statement(initializer, condition, next, body)

    def parse_continue_statement(self):
        """
        ContinueStatement ::
          'continue' Identifier? ';'
        """
        self.expect(CONTINUE)
        label = None
        if self.has_line_terminator_before_next():
            return self.create_continue_statement(label)
        if self.peek() == IDENTIFIER:
            label = self.expect(IDENTIFIER).value
        self.expect_semicolon()
        return self.create_continue_statement(label)

    def parse_break_statement(self):
        """
        BreakStatement ::
          'break' Identifier? ';'
        """
        self.expect(BREAK)
        label = None
        if not self.has_line_terminator_before_next():
            if self.peek() == IDENTIFIER:
                label = self.expect(IDENTIFIER).value
        self.expect_semicolon()
        return self.create_break_statement(label)

    def parse_return_statement(self):
        """
        ReturnStatement ::
          'return' Expression? ';'
        """
        self.expect(RETURN)
        expression = None
        if not self.has_line_terminator_before_next():
            if self.peek() not in (SEMICOLON, RIGHT_CURLY_BRACE, EOF):
                expression = self.parse_expression()
        self.expect_semicolon()
        return self.create_return_statement(expression)

    def parse_with_statement(self):
        """
        WithStatement ::
          'with' '(' Expression ')' Statement
        """
        self.expect(WITH)
        self.expect(LEFT_PAREN)
        expression = self.parse_expression()
        self.expect(RIGHT_PAREN)
        statement = self.parse_statement()
        return self.create_with_statement(expression, statement)

    def parse_case_clause(self):
        """
        CaseClause ::
          'case' Expression ':' Statement*
          'default' ':' Statement*
        """
        if self.peek() == CASE:
            self.expect(CASE)
            label = self.parse_expression()
        else:
            self.expect(DEFAULT)
            label = None
        self.expect(COLON)
        statements = []
        while self.peek() not in (CASE, DEFAULT, RIGHT_CURLY_BRACE, EOF):
            statements.append(self.parse_statement())
        return self.create_case_clause(label, statements)

    def parse_switch_statement(self):
        """
        SwitchStatement ::
          'switch' '(' Expression ')' '{' CaseClause* '}'
        """
        self.expect(SWITCH)
        self.expect(LEFT_PAREN)
        expression = self.parse_expression()
        self.expect(RIGHT_PAREN)
        self.expect(LEFT_CURLY_BRACE)
        cases = []
        while self.peek() != RIGHT_CURLY_BRACE:
            cases.append(self.parse_case_clause())
        self.expect(RIGHT_CURLY_BRACE)
        return self.create_switch_statement(expression, cases)

    def parse_throw_statement(self):
        """
        ThrowStatement ::
          'throw' Expression ';'
        """
        self.expect(THROW)
        expression = None
        if self.has_line_terminator_before_next():
            raise ParseException()
        expression = self.parse_expression()
        self.expect_semicolon()
        return self.create_throw(expression)

    def parse_try_statement(self):
        """
        TryStatement ::
          'try' Block Catch
          'try' Block Finally
          'try' Block Catch Finally

        Catch ::
          'catch' '(' Identifier ')' Block

        Finally ::
          'finally' Block
        """
        self.expect(TRY)
        try_block = self.parse_block_statement()
        catch_block = None
        name = None
        finally_block = None
        next = self.peek()
        if next == EOF or next not in (CATCH, FINALLY):
            raise ParseException("Expected 'catch' or 'finally'")

        if next == CATCH:
            self.expect(CATCH)
            self.expect(LEFT_PAREN)
            name = self.expect(IDENTIFIER).value
            self.expect(RIGHT_PAREN)
            catch_block = self.parse_block_statement()
            next = self.peek()

        if next == FINALLY:
            self.expect(FINALLY)
            finally_block = self.parse_block_statement()

        return self.create_try_statement(try_block, name, catch_block, finally_block)

    #
    # Function parsing
    #
    

    def parse_function_declaration(self):
        """
        FunctionDeclaration ::
          'function' Identifier '(' ParameterList? ')' '{' FunctionBody '}'
        """
        return self.create_function_declaration(*self.parse_function())

    def parse_function_expression(self):
        """
        FunctionDeclaration ::
          'function' Identifier? '(' ParameterList? ')' '{' FunctionBody '}'
        """
        return self.create_function_expression(*self.parse_function())
    
    def parse_function(self):
        """
        Generalized function parser.
        """
        self.expect(FUNCTION)
        name = None
        if self.peek() == IDENTIFIER:
            name = self.expect(IDENTIFIER).value
        self.expect(LEFT_PAREN)
        parameters = self.parse_parameter_list()
        self.expect(RIGHT_PAREN)
        body = self.parse_function_body()
        return (name, parameters, body)

    def parse_parameter_list(self):
        """
        ParameterList ::
          Identifier
          ParameterList , Identifier
        """
        parameters = []
        done = (self.peek() == RIGHT_PAREN)
        while not done:
            parameters.append(self.expect(IDENTIFIER).value)            
            done = (self.peek() == RIGHT_PAREN)
            if not done:
                self.expect(COMMA)
        return self.create_parameters(parameters)

    def parse_function_body(self):
        """
        FunctionBody ::
          SourceElements
        """
        self.expect(LEFT_CURLY_BRACE)
        statements = self.parse_source_elements(RIGHT_CURLY_BRACE)
        self.expect(RIGHT_CURLY_BRACE)
        return statements

    def parse_source_elements(self, until=EOF):
        """
        SourceElements::
          (Statement)* <end_token>
        """
        statements = []
        while self.peek() != until:
            if self.peek() == FUNCTION:
                statements.append(self.parse_function_declaration())
            else:
                statements.append(self.parse_statement())
        return statements

    def parse_program(self):
        return self.parse_source_elements()

    def parse(self):
        return self.parse_source_elements()

class Parser(NodeFactory, BaseParser):
    """
    This class implements parsing with abstract syntax tree production.
    """
    pass

#
# Utilities
#

def make_string_parser(string, filename=None, line=0, column=0, encoding='utf-8'):
    """
    Make a parser for the given string.
    """
    from bigrig.scanner import make_string_scanner, TokenStreamAllowReserved
    scanner = make_string_scanner(
        string, filename, line, column, encoding
    )
    stream = TokenStreamAllowReserved(scanner)
    return Parser(stream)

def parse_string(string, filename=None, line=0, column=0, encoding='utf-8'):
    """
    Parse a given stream into an abstract syntax tree.
    """
    parser = make_string_parser(
        string, filename, line, column, encoding
    )
    return parser.parse()

def make_file_parser(fd, filename=None, line=0, column=0, encoding='utf-8'):
    """
    Make a parser for the given file.
    """
    from bigrig.scanner import make_file_scanner, TokenStreamAllowReserved
    scanner = make_file_scanner(
        fd, filename, line, column, encoding
    )
    stream = TokenStreamAllowReserved(scanner)
    return Parser(stream)

def parse_file(filename, line=0, column=0, encoding='utf-8'):
    """
    Parse the file specified by filename into an abstract syntax tree.
    """
    fd = open(filename, 'rb')
    parser = make_file_parser(fd, filename, line, column, encoding)
    return parser.parse()
