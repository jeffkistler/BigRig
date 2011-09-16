"""
Unit tests for the parser.
"""
import unittest

class TestParser(unittest.TestCase):
    def setUp(self):
        self._parser_module = None

    def getParserModule(self):
        if self._parser_module is None:
            from bigrig import parser
            self._parser_module = parser
        return self._parser_module

    def makeStringParser(self, string):
        parse_mod = self.getParserModule()
        return parse_mod.make_string_parser(string)

    def parseString(self, string):
        parse_mod = self.getParserModule()
        return parse_mod.parse_string(string)

    def assertIsNode(self, expected, result, msg=None):
        classname = result.__class__.__name__
        self.assertEqual(expected, classname, msg=msg)

    #
    # Literals
    #

    def testParseObjectLiteralIdentifierKey(self):
        string = "{foo:1}"
        parser = self.makeStringParser(string)
        result = parser.parse_object_literal()
        self.assertIsNode('ObjectLiteral', result)
        self.assertEquals(1, len(result.properties))
        property = result.properties[0]
        self.assertIsNode('ObjectProperty', property)
        self.assertIsNode('PropertyName', property.name)
        self.assertIsNode('NumberLiteral', property.value)

    def testParseObjectLiteralStringLiteralKey(self):
        string = "{'foo':1}"
        parser = self.makeStringParser(string)
        result = parser.parse_object_literal()
        self.assertIsNode('ObjectLiteral', result)
        self.assertEquals(1, len(result.properties))
        property = result.properties[0]
        self.assertIsNode('ObjectProperty', property)
        self.assertIsNode('StringLiteral', property.name)
        self.assertIsNode('NumberLiteral', property.value)

    def testParseObjectLiteralNumberLiteralKey(self):
        string = "{0:1}"
        parser = self.makeStringParser(string)
        result = parser.parse_object_literal()
        self.assertIsNode('ObjectLiteral', result)
        self.assertEquals(1, len(result.properties))
        property = result.properties[0]
        self.assertIsNode('ObjectProperty', property)
        self.assertIsNode('NumberLiteral', property.name)
        self.assertIsNode('NumberLiteral', property.value)

    def testParseObjectLiteralInvalidKey(self):
        ParseException = self.getParserModule().ParseException
        string = "{function key(){}: value}"
        parser = self.makeStringParser(string)
        self.assertRaises(ParseException, parser.parse_object_literal)

    def testParseObjectLiteralMultipleProperties(self):
        string = '{"foo": "bar", baz: quux, 0: 1}'
        parser = self.makeStringParser(string)
        result = parser.parse_object_literal()
        self.assertIsNode('ObjectLiteral', result)
        self.assertEqual(3, len(result.properties))
        for i in range(3):
            self.assertIsNode('ObjectProperty', result.properties[i])

    def testParseArrayLiteral(self):
        string = "[1, 2, 3]"
        parser = self.makeStringParser(string)
        result = parser.parse_array_literal()
        self.assertIsNode('ArrayLiteral', result)
        self.assertEquals(3, len(result.elements))
        for i in xrange(3):
            self.assertIsNode('NumberLiteral', result.elements[i])

    def testParseRegExpLiteral(self):
        string = "/a*/gi"
        parser = self.makeStringParser(string)
        result = parser.parse_regexp_literal()
        self.assertIsNode('RegExpLiteral', result)
        self.assertEquals("/a*/", result.pattern)
        self.assertEquals("gi", result.flags)
        string = "/"
        parser = self.makeStringParser(string)
        ParseException = self.getParserModule().ParseException
        self.assertRaises(ParseException, parser.parse_regexp_literal)
        string = '/*./gi'
        parser = self.makeStringParser(string)
        self.assertRaises(ParseException, parser.parse_regexp_literal)

    #
    # Expressions
    #

    def testParsePrimaryExpressions(self):
        testCases = {
            'parse-this': ('this', 'ThisNode'),
            'parse-null': ('null', 'NullNode'),
            'parse-true': ('true', 'TrueNode'),
            'parse-false': ('false', 'FalseNode'),
            'parse-ident': ('someIdentifier', 'Name'),
            'parse-array': ('[1,2,3]', 'ArrayLiteral'),
            'parse-obj': ('{foo:bar}', 'ObjectLiteral'),
            'parse-regex': ('/^foo$/g', 'RegExpLiteral'),
        }
        for test_name, (string, expected) in testCases.iteritems():
            parser = self.makeStringParser(string)
            result = parser.parse_primary_expression()
            fmt_args = (test_name, expected, result.__class__.__name__)
            msg = '%s did not parse an %s; got %s' % fmt_args
            self.assertIsNode(expected, result, msg=msg)

    def testParseMemberExpressionDotProperty(self):
        string = "foo.bar"
        parser = self.makeStringParser(string)
        result = parser.parse_member_expression()
        self.assertIsNode('DotProperty', result)

    def testParseMemberExpressionBracketPropertyStringLiteralKey(self):
        string = "foo['bar']"
        parser = self.makeStringParser(string)
        result = parser.parse_member_expression()
        self.assertIsNode('BracketProperty', result)

    def testParseMemberExpressionBracketPropertyIdentifierKey(self):
        string = "foo[bar]"
        parser = self.makeStringParser(string)
        result = parser.parse_member_expression()
        self.assertIsNode('BracketProperty', result)

    def testParseMemberExpressionComplexProperties(self):
        string = "foo.baz['bar']"
        parser = self.makeStringParser(string)
        result = parser.parse_member_expression()
        self.assertIsNode('BracketProperty', result)
        self.assertIsNode('DotProperty', result.object)

    def testParseMemberExpressionCall(self):
        string = "foo.bar('bar')"
        parser = self.makeStringParser(string)
        result = parser.parse_member_expression()
        self.assertIsNode('CallExpression', result)
        self.assertIsNode('DotProperty', result.expression)

    def testParseMemberExpressionComplexCall(self):
        string = "foo.bar[baz]('bar')"
        parser = self.makeStringParser(string)
        result = parser.parse_member_expression()
        self.assertIsNode('CallExpression', result)
        self.assertIsNode('BracketProperty', result.expression)
        self.assertIsNode('DotProperty', result.expression.object)

    def testParseMemberExpressionCallMultipleArguments(self):
        string = 'foo.bar(baz, quux, false)'
        parser = self.makeStringParser(string)
        result = parser.parse_member_expression()
        self.assertIsNode('CallExpression', result)
        self.assertEqual(3, len(result.arguments))

    def testParseMemberExpressionNewNoArguments(self):
        string = "new foo"
        ParseException = self.getParserModule().ParseException
        parser = self.makeStringParser(string)
        self.assertRaises(ParseException, parser.parse_member_expression)

    def testParseMemberExpressionNewArguments(self):
        string = "new foo(bar)"
        parser = self.makeStringParser(string)
        result = parser.parse_member_expression()
        self.assertIsNode('NewExpression', result)
        self.assertEqual(1, len(result.arguments))

    def testParseMemberExpressionNewCompilcated(self):
        string = "new Something(argument1, argument2).method()[property]"
        parser = self.makeStringParser(string)
        result = parser.parse_member_expression()
        self.assertIsNode('BracketProperty', result)
        self.assertIsNode('CallExpression', result.object)
        self.assertIsNode('DotProperty', result.object.expression)
        self.assertIsNode('NewExpression', result.object.expression.object)
        
    def testParseMemberExpressionFunctionExpression(self):
        string = 'function(){;}'
        parser = self.makeStringParser(string)
        result = parser.parse_member_expression()
        self.assertIsNode('FunctionExpression', result)

    def testParseUnaryExpression(self):
        testCases = {
            'parse-not': ('!a', 'UnaryOperation'),
            'parse-negate': ('-a', 'UnaryOperation'),
            'parse-positive': ('+a', 'UnaryOperation'),
            'parse-bitnot': ('~a', 'UnaryOperation'),
            'parse-delete': ('delete a', 'DeleteOperation'),
            'parse-void': ('void a', 'VoidOperation'),
            'parse-typeof': ('typeof a', 'TypeofOperation'),
            'parse-prefix-count-plus': ('++a', 'PrefixCountOperation'),
            'parse-prefix-count-minus': ('--a', 'PrefixCountOperation'),
        }
        for test_name, (string, expected) in testCases.iteritems():
            parser = self.makeStringParser(string)
            result = parser.parse_unary_expression()
            fmt_args = (test_name, expected, result.__class__.__name__)
            msg = '%s did not parse an %s; got %s' % fmt_args
            self.assertIsNode(expected, result, msg=msg)

    def testParsePostfixExpression(self):
        testCases = [
            '(!a)++',
            '(a+b)++',
            'd--',
            '1--',
        ]
        for testCase in testCases:
            parser = self.makeStringParser(testCase)
            result = parser.parse_unary_expression()
            self.assertIsNode('PostfixCountOperation', result)

    def testParseBinaryOperatorExpressionPrecedence(self):
        string = "3 + 4 * 5"
        parser = self.makeStringParser(string)
        result = parser.parse_expression()
        self.assertIsNode('BinaryOperation', result)
        self.assertIsNode('BinaryOperation', result.right)
        self.assertIsNode('NumberLiteral', result.left)

    def testParseBinaryOperatorParenthesesPrecedence(self):
        string = "(3 + 4) * 5"
        parser = self.makeStringParser(string)
        result = parser.parse_expression()
        self.assertIsNode('BinaryOperation', result)
        self.assertIsNode('BinaryOperation', result.left)
        self.assertIsNode('NumberLiteral', result.right)

    def testParseBinaryOperatorMultiplePrecedence(self):
        string = "3 + 4 * 5 + 6"
        parser = self.makeStringParser(string)
        result = parser.parse_expression()
        self.assertIsNode('BinaryOperation', result)
        self.assertIsNode('NumberLiteral', result.left)
        self.assertIsNode('BinaryOperation', result.right)
        self.assertEquals('+', result.right.op)
        self.assertIsNode('BinaryOperation', result.right.left)
        self.assertEquals('*', result.right.left.op)

    def testParseBinaryOperatorComparison(self):
        string = "3 + 4 && 5 + 6"
        parser = self.makeStringParser(string)
        result = parser.parse_expression()
        self.assertIsNode('BinaryOperation', result)
        self.assertEquals('&&', result.op)
        self.assertIsNode('BinaryOperation', result.left)
        self.assertIsNode('BinaryOperation', result.right)

    def testParseAssignmentExpression(self):
        testCases = [
            'a = b',
            'a |= b',
            'a ^= b',
            'a &= b',
            'a <<= b',
            'a >>= b',
            'a >>>= b,',
            'a += b',
            'a -= b',
            'a *= b',
            'a /= b',
            'a %= b',
            'a = b = c',
            'a = b += c',
        ]
        for string in testCases:
            parser = self.makeStringParser(string)
            result = parser.parse_assignment_expression()
            self.assertIsNode('Assignment', result)

    def testParseAssignmentExpressionInvalid(self):
        testCases = [
            '1 = 2',
            '"a" ^= c',
            'null = 2',
        ]
        ParseException = self.getParserModule().ParseException
        for string in testCases:
            parser = self.makeStringParser(string)
            self.assertRaises(ParseException, parser.parse_assignment_expression)

    def testParseConditionalExpression(self):
        string = 'a ? b:c'
        parser = self.makeStringParser(string)
        result = parser.parse_conditional_expression()
        self.assertIsNode('Conditional', result)

    def testParseConditionalInvalid(self):
        testCases = [
            'a ? b',
            'a ?:b',
        ]
        ParseException = self.getParserModule().ParseException
        for string in testCases:
            parser = self.makeStringParser(string)
            self.assertRaises(ParseException, parser.parse_conditional_expression)

    def testParseCommaExpression(self):
        testCases = [
            'a, b, c',
        ]
        for string in testCases:
            parser = self.makeStringParser(string)
            result = parser.parse_expression()
            self.assertIsNode('BinaryOperation', result)

    def testParseExpression(self):
        testCases = {
            'call-functionexpression': ('(function() { return {};})();', 'CallExpression'),
        }
        for test_name, (string, expected) in testCases.iteritems():
            parser = self.makeStringParser(string)
            result = parser.parse_expression()
            fmt_args = (test_name, expected, result.__class__.__name__)
            msg = '%s did not parse an %s; got %s' % fmt_args
            self.assertIsNode(expected, result, msg=msg)

    #
    # Statements
    #

    def testParseVariableStatement(self):
        string = "var foo = bar, baz;"
        parser = self.makeStringParser(string)
        result = parser.parse_variable_statement()
        self.assertIsNode('VariableStatement', result)
        self.assertEquals(2, len(result.declarations))

    def testParseIfStatement(self):
        testCases = [
            'if (x);',
            'if (x); else ;',
            'if (x) return; else if (y) print(y);',
            'if (x) { print(x); return; }',
            'if (x) {;} else {;}',
        ]
        for string in testCases:
            parser = self.makeStringParser(string)
            result = parser.parse_if_statement()
            self.assertIsNode('IfStatement', result)

    def parseIfStatementInvalid(self):
        testCases = [
            'if (x) else y;',
            'if x return;',
        ]
        ParseException = self.getParserModule().ParseException
        for string in testCases:
            parser = self.makeStringParser(string)
            self.assertRaises(ParseException, parser.parse_if_statement)

    def testParseWhileStatement(self):
        testCases = [
            'while (true);',
            'while (x < y) print(x);',
            'while (x < y) { print(x); print(y); }',
        ]
        for string in testCases:
            parser = self.makeStringParser(string)
            result = parser.parse_while_statement()
            self.assertIsNode('WhileStatement', result)

    def parseWhileStatementInvalid(self):
        testCases = [
            'while x {;}',
            'while (true)',
        ]
        ParseException = self.getParserModule().ParseException
        for string in testCases:
            parser = self.makeStringParser(string)
            self.assertRaises(ParseException, parser.parse_while_statement)

    def testParseDoWhileStatement(self):
        testCases = [
            'do print(x); while(true);',
            'do { print(x); } while(x);',
            'do { print(x); x += 1; } while(x < y);',
            'do;while(true);',
        ]
        for string in testCases:
            parser = self.makeStringParser(string)
            result = parser.parse_do_while_statement()
            self.assertIsNode('DoWhileStatement', result)

    def parseDoWhileStatementInvalid(self):
        testCases = [
            'do;while true',
            'do;while(true)',
        ]
        ParseException = self.getParserModule().ParseException
        for string in testCases:
            parser = self.makeStringParser(string)
            self.assertRaises(ParseException, parser.parse_do_while_statement)

    def testParseWithStatement(self):
        testCases = [
            'with (x) { a = true; }',
        ]
        for string in testCases:
            parser = self.makeStringParser(string)
            result = parser.parse_with_statement()
            self.assertIsNode('WithStatement', result)

    def testParseWithStatementInvalid(self):
        testCases = [
            'with x { a = true; }',
        ]
        ParseException = self.getParserModule().ParseException
        for string in testCases:
            parser = self.makeStringParser(string)
            self.assertRaises(ParseException, parser.parse_with_statement)

    def testParseForStatement(self):
        testCases = [
            'for (;;);',
            'for (var i=0,j=0;;) {}',
            'for ((x in b); c; u) {}',
            'for (;x in b;) {},',
            'for (;x in b;) { for (var a in b) print(a); },',
        ]
        for string in testCases:
            parser = self.makeStringParser(string)
            result = parser.parse_for_statement()
            self.assertIsNode('ForStatement', result)

    def testParseForInStatement(self):
        testCases = [
            'for (var x in b);',
            'for(x in b) { print(x); }',
        ]
        for string in testCases:
            parser = self.makeStringParser(string)
            result = parser.parse_for_statement()
            self.assertIsNode('ForInStatement', result)

    def testParseReturnStatement(self):
        testCases = [
            'return /* comment */;',
            'return label;',
            'return\nlabel;',
            'return a + b;',
        ]
        for string in testCases:
            parser = self.makeStringParser(string)
            result = parser.parse_return_statement()
            self.assertIsNode('ReturnStatement', result)

    def testParseContinueStatement(self):
        testCases = [
            'continue /* comment */;',
            'continue label;',
            'continue\nlabel;',
        ]
        for string in testCases:
            parser = self.makeStringParser(string)
            result = parser.parse_continue_statement()
            self.assertIsNode('ContinueStatement', result)

    def testParseBreakStatement(self):
        testCases = [
            'break /* comment */;',
            'break label;',
            'break\nlabel;',
        ]
        for string in testCases:
            parser = self.makeStringParser(string)
            result = parser.parse_break_statement()
            self.assertIsNode('BreakStatement', result)

    def testParseLabelledStatement(self):
        string = 'foo: bar;'
        parser = self.makeStringParser(string)
        result = parser.parse_expression_statement()
        self.assertIsNode('LabelledStatement', result)

    def testParseCaseClause(self):
        testCases = [
            'case foo:;',
            'case bar: baz;',
            'case 0:;',
            'default: return;',
            'case "b": doSomething(); break;',
        ]
        for string in testCases:
            parser = self.makeStringParser(string)
            result = parser.parse_case_clause()
            self.assertIsNode('CaseClause', result)

    def testParseCaseClauseInvalid(self):
        testCases = [
            'case:;',
        ]
        ParseException = self.getParserModule().ParseException
        for string in testCases:
            parser = self.makeStringParser(string)
            self.assertRaises(ParseException, parser.parse_case_clause)

    def testParseSwitchStatement(self):
        testCases = [
            'switch(n) { case 1: break; case 2: break; default: print(n)}',
        ]
        for string in testCases:
            parser = self.makeStringParser(string)
            result = parser.parse_switch_statement()
            self.assertIsNode('SwitchStatement', result)

    def testParseThrowStatement(self):
        testCases = [
            'throw a;',
            'throw a + 5',
        ]
        for string in testCases:
            parser = self.makeStringParser(string)
            result = parser.parse_throw_statement()
            self.assertIsNode('Throw', result)

    def testParseThrowStatementInvalid(self):
        testCases = [
            'throw;',
            'throw\na;',
        ]
        ParseException = self.getParserModule().ParseException
        for string in testCases:
            parser = self.makeStringParser(string)
            self.assertRaises(ParseException, parser.parse_throw_statement)

    def testParseTryStatement(self):
        testCases = [
            'try { ; } catch(e) { ; }',
            'try { ; } catch(e) { ; } finally { ; }',
        ]
        for string in testCases:
            parser = self.makeStringParser(string)
            result = parser.parse_try_statement()
            self.assertIsNode('TryStatement', result)

    def testParseTryStatementInvalid(self):
        testCases = [
            'try {;}',
            'try { ; } catch {}',
        ]
        ParseException = self.getParserModule().ParseException
        for string in testCases:
            parser = self.makeStringParser(string)
            self.assertRaises(ParseException, parser.parse_try_statement)

    def testParseFunctionDeclaration(self):
        testCases = [
            'function foo() { return 5; }'
            'function bar(a) { ; }',
            'function baz(a,b,c) {;}',
            'function baz(a,b,c) { function foo() {;} }',
        ]
        for string in testCases:
            parser = self.makeStringParser(string)
            result = parser.parse_function_declaration()
            self.assertIsNode('FunctionDeclaration', result)

    #
    # General parsing
    #

    def testValidPrograms(self):
        testPrograms = [
            'do s; while(e);',
            'for (x in b);',
            'for (;;);',
            'for (var i=0,j=0;;) {}',
            'for ((x in b); c; u) {}',
            'for (;x in b;) {}',
            'continue /* comment */;',
            'continue label;',
            'try { ; } catch(e) { ; }',
            'try { ; } catch(e) { ; } finally { ; }',
        ]
        ParseException = self.getParserModule().ParseException
        for program in testPrograms:
            try:
                result = self.parseString(program)
            except ParseException:
                self.fail('Valid program "%s" failed to parse' % program)

    def testInvalidPrograms(self):
        testPrograms = [
            'for (x in b; c; u) {}',
            'throw\n',
            'throw\n;',
            'throw;',
            'if (a > b)\nelse c = d',
        ]
        ParseException = self.getParserModule().ParseException
        for program in testPrograms:
            try:
                self.parseString(program)
                self.fail('Invalid program "%s" parsed without error' % program)
            except ParseException:
                continue

    def testSemicolonInsertion(self):
        testPrograms = {
            'test-continue-noexpr': ('continue\n', 'continue;'),
            'test-multiline-primaries': ('x\ny\nz', 'x;y;z;'),
            'test-multiline-assignment': ('x=1\ny=2\nz=3', 'x=1;y=2;z=3'),
            'test-return-newline-expr1': ('return\n1;', 'return;1;'),
            'test-return-newline-expr2': ('return\na+b', 'return;a+b;'),
            'test-multiline-prefix': ('a = b\n++c', 'a=b;++c;'),
            'test-multiline-call': ('a = b + c\n(d + e)', 'a = b + c(d + e);'),
        }
        for test_name, (string, expected) in testPrograms.iteritems():
            parser = self.makeStringParser(string)
            result = parser.parse_program()
            parser = self.makeStringParser(expected)
            expected = parser.parse_program()
            self.assertEqual(len(expected), len(result))
