# -*- coding: utf-8 -*-
"""
Test the lexical scanner.
"""
import unittest

class TestScanner(unittest.TestCase):
    def setUp(self):
        self._scanner_module = None

    def getScannerModule(self):
        if self._scanner_module is None:
            from bigrig.parser import scanner
            self._scanner_module = scanner
        return self._scanner_module

    def makeStringScanner(self, string):
        scanner = self.getScannerModule()
        return scanner.make_string_scanner(string)

    def getSingleToken(self, string):
        scanner = self.makeStringScanner(string)
        token = scanner.next()
        self.assertTokenTypeEqual('EOF', scanner.next())
        return token

    def assertTokenTypeEqual(self, type, token):
        message = "%s: '%s' is not a %s token" % (token.type, token.value, type)
        self.assertEqual(type, token.type, msg=message)

    def assertTokenValueEqual(self, value, token):
        self.assertEqual(value, token.value)

    def assertTokenTypeValueEqual(self, type, value, token):
        self.assertTokenTypeEqual(type, token)
        self.assertTokenValueEqual(value, token)

    def testScanOperators(self):
        tests = [
            ('<', 'LT'),
            ('<=', 'LE'),
            ('<<', 'LSH'),
            ('<<=', 'ASSIGN_LSH'),
            ('>', 'GT'),
            ('>=', 'GE'),
            ('>>', 'RSH'),
            ('>>=', 'ASSIGN_RSH'),
            ('>>>', 'URSH'),
            ('>>>=', 'ASSIGN_URSH'),
            ('=', 'ASSIGN'),
            ('==', 'EQ'),
            ('===', 'SHEQ'),
            ('!', 'NOT'),
            ('!=', 'NE'),
            ('!==', 'SHNE'),
            ('+', 'ADD'),
            ('+=', 'ASSIGN_ADD'),
            ('++', 'INC'),
            ('-', 'SUB'),
            ('-=', 'ASSIGN_SUB'),
            ('--', 'DEC'),
            ('&', 'BITAND'),
            ('&&', 'AND'),
            ('&=', 'ASSIGN_BITAND'),
            ('|', 'BITOR'),
            ('||', 'OR'),
            ('|=', 'ASSIGN_BITOR'),
            ('*', 'MUL'),
            ('*=', 'ASSIGN_MUL'),
            ('%', 'MOD'),
            ('%=', 'ASSIGN_MOD'),
            ('^', 'BITXOR'),
            ('^=', 'ASSIGN_BITXOR'),
            ('.', 'DOT'),
        ]
        for i, (string, type) in enumerate(tests):
            token = self.getSingleToken(string)
            self.assertTokenTypeEqual(type, token)

    def testNumberScanning(self):
        tests = [
            ('5', 'INTEGER'),
            ('5.5', 'DECIMAL'),
            ('0', 'INTEGER'),
            ('0.0', 'DECIMAL'),
            ('0.001', 'DECIMAL'),
            ('1.e2', 'DECIMAL'),
            ('1.e-2', 'DECIMAL'),
            ('1.E2', 'DECIMAL'),
            ('1.E-2', 'DECIMAL'),
            ('.5', 'DECIMAL'),
            ('.5e3', 'DECIMAL'),
            ('.5e-3', 'DECIMAL'),
            ('0.5e3', 'DECIMAL'),
            ('55', 'INTEGER'),
            ('123', 'INTEGER'),
            ('55.55', 'DECIMAL'),
            ('55.55e10', 'DECIMAL'),
            ('123.456', 'DECIMAL'),
            ('123', 'INTEGER'),
            ('0x01', 'INTEGER'),
            ('0XCAFE', 'INTEGER'),
            ('0x12345678', 'INTEGER'),
            ('0x1234ABCD', 'INTEGER'),
            ('0xab', 'INTEGER'),
            ('0x0001', 'INTEGER'),
        ]
        for i, (string, type) in enumerate(tests):
            token = self.getSingleToken(string)
            self.assertTokenTypeValueEqual(type, string, token)

    def testKeywordScanning(self):
        tests = [
            ('false', 'FALSE'),
            ('in', 'IN'),
            ('null', 'NULL'),
            ('if', 'IF'),
            ('for', 'FOR'),
            ('true', 'TRUE'),
            ('switch', 'SWITCH'),
            ('finally', 'FINALLY'),
            ('var', 'VAR'),
            ('new', 'NEW'),
            ('function', 'FUNCTION'),
            ('do', 'DO'),
            ('return', 'RETURN'),
            ('void', 'VOID'),
            ('else', 'ELSE'),
            ('break', 'BREAK'),
            ('catch', 'CATCH'),
            ('instanceof', 'INSTANCEOF'),
            ('with', 'WITH'),
            ('throw', 'THROW'),
            ('case', 'CASE'),
            ('default', 'DEFAULT'),
            ('try', 'TRY'),
            ('this', 'THIS'),
            ('while', 'WHILE'),
            ('continue', 'CONTINUE'),
            ('typeof', 'TYPEOF'),
            ('delete', 'DELETE'),
        ]
        for i, (string, type) in enumerate(tests):
            token = self.getSingleToken(string)
            self.assertTokenTypeValueEqual(type, string, token)

    def testReservedWordScanning(self):
        tests = [
            ('debugger', 'RESERVED'),
            ('synchronized', 'RESERVED'),
            ('int', 'RESERVED'),
            ('abstract', 'RESERVED'),
            ('float', 'RESERVED'),
            ('private', 'RESERVED'),
            ('char', 'RESERVED'),
            ('boolean', 'RESERVED'),
            ('export', 'RESERVED'),
            ('native', 'RESERVED'),
            ('const', 'RESERVED'),
            ('long', 'RESERVED'),
            ('extends', 'RESERVED'),
            ('volatile', 'RESERVED'),
            ('final', 'RESERVED'),
            ('goto', 'RESERVED'),
            ('enum', 'RESERVED'),
            ('transient', 'RESERVED'),
            ('import', 'RESERVED'),
            ('interface', 'RESERVED'),
            ('byte', 'RESERVED'),
            ('super', 'RESERVED'),
            ('class', 'RESERVED'),
            ('implements', 'RESERVED'),
            ('short', 'RESERVED'),
            ('package', 'RESERVED'),
            ('double', 'RESERVED'),
            ('public', 'RESERVED'),
            ('protected', 'RESERVED'),
            ('static', 'RESERVED'),
            ('throws', 'RESERVED'),
        ]
        for i, (string, type) in enumerate(tests):
            token = self.getSingleToken(string)
            self.assertTokenTypeValueEqual(type, string, token)

    def testSingleCharTokenScanning(self):
        tests = [
            ('!', 'NOT'),
            ('%', 'MOD'),
            ('|', 'BITOR'),
            ('&', 'BITAND'),
            (')', 'RIGHT_PAREN'),
            ('(', 'LEFT_PAREN'),
            ('+', 'ADD'),
            ('*', 'MUL'),
            ('-', 'SUB'),
            (',', 'COMMA'),
            ('/', 'DIV'),
            ('.', 'DOT'),
            (';', 'SEMICOLON'),
            (':', 'COLON'),
            ('=', 'ASSIGN'),
            ('<', 'LT'),
            ('?', 'HOOK'),
            ('>', 'GT'),
            ('[', 'LEFT_BRACKET'),
            (']', 'RIGHT_BRACKET'),
            ('^', 'BITXOR'),
            ('{', 'LEFT_CURLY_BRACE'),
            ('}', 'RIGHT_CURLY_BRACE'),
            ('~', 'BITNOT'),
        ]
        for i, (string, type) in enumerate(tests):
            token = self.getSingleToken(string)
            self.assertTokenTypeValueEqual(type, string, token)

    def testCommentScanning(self):
        tests = [
            '// Single line',
            '/* multiline, but on a single */',
            '/* Multiple\r\nlines */',
            '/* Multiple\nlines*\nwith***stars */',
        ]
        for string in tests:
            token = self.getSingleToken(string)
            self.assertTokenTypeEqual('COMMENT', token)

    def testRegExpScanning(self):
        tests = [
            r'/^foo$/',
            r'/^[a-z]+/',
            '/^\\\\n/',
            r'/\[/',
            r'/[i]/',
            r'/[\]]/',
            r'/a[\]]/',
            r'/a[\]]b/',
            r'/[\]/]/gi',
            r'/\[[^\]]+\]/gi',
            r'/^(?!\d)(?:\w)+|^"(?:[^"]|"")+"/',
            r'/^@(?:(?!\d)(?:\w|\:)+|^"(?:[^"]|"")+")\[[^\]]+\]/',
            r"/^'(?:[^']|'')*'/",
            r'/^[0-9]+(?:\.[0-9]*(?:[eE][-+][0-9]+)?)?/',
            r'/^(?:==|=|<>|<=|<|>=|>|!~~|!~|~~|~|!==|!=|!~=|!~|!|&|\||\.|\:|,|\(|\)|\[|\]|\{|\}|\?|\:|;|@|\^|\/\+|\/|\*|\+|-)/',
        ]
        for string in tests:
            scanner = self.makeStringScanner(string)
            start = scanner.next()
            self.assertTokenTypeEqual('DIV', start)
            pattern = scanner.scan_regexp()
            flags = scanner.scan_regexp_flags()
            eof = scanner.next()
            self.assertTokenTypeEqual('REGEXP', pattern)
            self.assertTokenTypeEqual('EOF', eof)
            

    def testIdentifierScanning(self):
        tests = [
            r'\u1234xyz',
            r'$',
            r'$_',
            r'$\u0123',
            r'_',
            r'a123',
            r'\u0065_\u0067',
        ]
        for string in tests:
            token = self.getSingleToken(string)
            self.assertTokenTypeEqual('IDENTIFIER', token)

    def testStringScanning(self):
        tests = [
            r'"string"',
            r"'string'",
            r'"ƃuıxǝ⅂ ʇdıɹɔsɐʌɐſ\""',
            r"'don\'t'", 
            "'foo\\\nbar'",
            r'"Some hex escapeage: \x32"',
            r'"Some unicode escapeage: \u1234"',
            r'"Hello \"th/foo/ere\""',
            r'"He\x23llo \'th/foo/ere\'"',
            r'"slash quote \", just quote \""',
        ]
        for string in tests:
            token = self.getSingleToken(string)
            self.assertTokenTypeEqual('STRING', token)
