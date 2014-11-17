"""
Parsing support for ECMAScript literal values.
"""
from .exceptions import ESSyntaxError

DECIMAL_DIGITS = set(u'0123456789')
NONZERO_DECIMAL_DIGITS = set(u'123456789')
OCTAL_DIGITS = set(u'01234567')
ZERO_TO_THREE = set(u'0123')
FOUR_TO_SEVEN = set(u'4567')
HEX_DIGITS = set(u'0123456789abcdefABCDEF')
SINGLE_ESCAPE_CHARS = {
    u'b': u'\b',
    u't': u'\t',
    u'n': u'\n',
    u'v': u'\v',
    u'f': u'\f',
    u'r': u'\r',
    u'"': u'"',
    u'\'': u'\'',
    u'\\': u'\\',
}
LINE_TERMINATORS = set('\u000A\u000D\u2028\u2029'.decode('unicode-escape'))
CONTROL_CLASS_CHARS = set(u'dDsSw')
CONTROL_ESCAPE_CHARS = set(u'tnvfr')
CONTROL_LETTERS = set(u'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ')
NaN = float('nan')


class LiteralParseError(Exception):
    """
    Invalid literal production.
    """
    pass


class LiteralParser(object):
    """
    Base parser class for parsing literal strings.
    """
    def __init__(self, string):
        self.string = string
        self.pos = -1

    def peek(self, num_chars=1):
        index = self.pos + num_chars
        if index >= len(self.string):
            return u''
        return self.string[index]

    def advance(self):
        self.pos = self.pos + 1
        if self.pos < len(self.string):
            return self.string[self.pos]
        return u''

    def expect(self, char):
        next_char = self.peek()
        if next_char != char:
            raise LiteralParseError('Unexpected char')
        return self.advance()

    @classmethod
    def parse_string(cls, string, **kwargs):
        parser = cls(string, **kwargs)
        return parser.parse()


class IdentifierParser(LiteralParser):
    """
    Parse and return identifier value with escapes computed.
    """
    def parse_unicode_escape(self):
        self.expect(u'\\')
        self.expect(u'u')
        chars = []
        for i in range(4):
            if self.peek() not in HEX_DIGITS:
                raise ESSyntaxError('Invalid identifier: %s' % self.string)
            chars.append(self.advance())
        char = unichr(int(u''.join(chars), 16))
        if char not in HEX_DIGITS:
            raise ESSyntaxError('Invalid identifier: %s' % self.string)
        return char

    def parse(self):
        chars = []
        while self.pos < len(self.string):
            if self.peek() == u'\\':
                char = self.parse_unicode_escape()
            else:
                char = self.advance()
            chars.append(char)
        return u''.join(chars)


class NumberLiteralParser(LiteralParser):
    """
    Parse integer and floating point numbers.
    """
    def __init__(self, string, allow_octal=True):
        super(NumberLiteralParser, self).__init__(string)
        self.allow_octal = allow_octal

    def parse_hex_literal(self):
        digits = []
        char = self.peek()
        if char != u'0':
            raise ESSyntaxError('Invalid number literal')
        self.advance()
        char = self.peek()
        if char not in (u'x', u'X'):
            raise ESSyntaxError('Invalid number literal')
        self.advance()
        char = self.peek()
        while char in HEX_DIGITS:
            digits.append(char)
            self.advance()
            char = self.peek()
        if char != u'':
            raise ESSyntaxError('Invalid number literal') 
        if not digits:
            raise ESSyntaxError('Invalid number literal')
        return int(u''.join(digits), 16)

    def parse_octal_literal(self):
        digits = []
        char = self.peek()
        if char != u'0':
            raise ESSyntaxError('Invalid number literal')
        self.advance()
        char = self.peek()
        while char in OCTAL_DIGITS:
            digits.append(char)
            self.advance()
            char = self.peek()
        if char != u'':
            if char in DECIMAL_DIGITS:
                return self.parse_decimal_literal(digits)
            raise ESSyntaxError('Invalid number literal')
        return int(u''.join(digits), 8)

    def parse_decimal_literal(self, digits=None):
        if digits is None:
            digits = []
        decimal_digits = []
        power_sign = 1
        power_digits = []
        while self.peek() in DECIMAL_DIGITS:
            digits.append(self.peek())
            self.advance()
        if self.peek() == u'.':
            self.advance()
            while self.peek() in DECIMAL_DIGITS:
                decimal_digits.append(self.peek())
                self.advance()
        if self.peek() in (u'e', u'E'):
            power_sign = 1
            self.advance()
            if self.peek() == u'-':
                power_sign = -1
                self.advance()
            elif self.peek() == u'+':
                self.advance()
            if self.peek() not in DECIMAL_DIGITS:
                raise ESSyntaxError('Invalid number literal')
            while self.peek() in DECIMAL_DIGITS:
                power_digits.append(self.peek())
                self.advance()
        if self.peek() != u'':
            raise ESSyntaxError('Invalid number literal')
        if digits:
            integral = int(u''.join(digits))
            if decimal_digits and power_digits:
                power = power_sign * int(u''.join(power_digits))
                decimal = int(u''.join(decimal_digits)) * (10 ** (power-len(decimal_digits)))
                return integral * (10 ** power) + decimal
            elif decimal_digits:
                return integral + (int(u''.join(decimal_digits)) * (10 ** -len(decimal_digits)))
            elif power_digits:
                power = power_sign * int(u''.join(power_digits))
                if power < 0 and digits[power:] and digits[:power] and int(u''.join(digits[power:])) == 0:
                    return int(u''.join(digits[:power]))
                return integral * (10 ** power)
            return integral
        elif decimal_digits:
            if power_digits:
                power = power_sign * int(u''.join(power_digits))
                return int(u''.join(decimal_digits)) * (10 ** (power - len(decimal_digits)))
            return int(u''.join(decimal_digits)) * (10 ** -len(decimal_digits))
        return NaN

    def parse(self):
        # This doesn't follow the spec exactly in that it allows leading 0 digits
        char = self.peek()
        if char == u'0':
            lookahead = self.peek(2)
            if lookahead in (u'x', u'X'):
                return self.parse_hex_literal()
        while char == u'0':
            if lookahead in OCTAL_DIGITS:
                if not self.allow_octal:
                    raise ESSyntaxError('Invalid number literal')
                return self.parse_octal_literal()
            elif lookahead == u'':
                return 0
            elif lookahead in (u'.', u'e', u'E'):
                break
            elif lookahead != '0':
                raise ESSyntaxError('Invalid number literal')
            self.advance()
            char = self.peek()
            lookahead = self.peek(2)
        return self.parse_decimal_literal()


class StringLiteralParser(LiteralParser):
    """
    Parse string literals, converting escapes to unicode characters.
    """
    # 7.8.4
    def __init__(self, string, allow_octal=False):
        super(StringLiteralParser, self).__init__(string)
        self.allow_octal = allow_octal

    def parse_octal_escape(self):
        char = self.peek()
        if char in OCTAL_DIGITS and self.peek(2) not in DECIMAL_DIGITS:
            self.advance()
            value = char
        elif char in ZERO_TO_THREE and self.peek(2) in OCTAL_DIGITS:
            take = 2
            if self.peek(3) in DECIMAL_DIGITS:
                take = 3
            value = u''.join(self.peek(i) for i in range(take))
            for i in range(take):
                self.advance()
        elif char in FOUR_TO_SEVEN and self.peek(2) in OCTAL_DIGITS:
            value = u''.join(self.peek(i) for i in range(2))
            for i in range(2):
                self.advance()
        else:
            raise ESSyntaxError('Invalid string literal')
        return unichr(int(value, 8))

    def parse_hex_digits(self, count):
        digits = []
        for i in range(count):
            char = self.peek()
            if char not in HEX_DIGITS:
                raise ESSyntaxError('Invalid string literal')
            digits.append(char)
            self.advance()
        return unichr(int(u''.join(digits), 16))

    def parse_escape(self):
        char = self.peek()
        if char != '\\':
            raise ESSyntaxError('Invalid string literal')
        self.advance()
        char = self.peek()
        if char == u'':
            raise ESSyntaxError('Invalid string literal')
        elif char == u'0' and self.peek(2) not in DECIMAL_DIGITS:
            self.advance()
            return u'\0'
        elif char in DECIMAL_DIGITS:
            if self.allow_octal:
                return self.parse_octal_escape()
            raise ESSyntaxError('Invalid string literal');
        elif char == u'x':
            self.advance()
            return self.parse_hex_digits(2)
        elif char == u'u':
            self.advance()
            return self.parse_hex_digits(4)
        elif char in SINGLE_ESCAPE_CHARS:
            self.advance()
            return SINGLE_ESCAPE_CHARS[char]
        elif char in LINE_TERMINATORS:
            self.advance()
            if char == u'\r' and self.peek() == u'\n':
                self.advance()
            return u''
        else:
            # Return the char
            self.advance()
        return char

    def parse(self):
        parts = []
        quote = self.peek()
        self.advance()
        while self.pos < len(self.string):
            char = self.peek()
            if char == quote:
                break
            elif char == '\\':
                parts.append(self.parse_escape())
            else:
                parts.append(char)
                self.advance()
        self.advance()
        if self.peek() != u'':
            raise ESSyntaxError('Invalid string literal')
        return u''.join(parts)


class RegExpParser(LiteralParser):
    """
    Parse regular expression literal strings, converting escapes to Python re
    syntax.
    """
    # 15.10.1
    def parse_hex_digits(self, count):
        digits = []
        for i in range(count):
            char = self.peek()
            if char not in HEX_DIGITS:
                raise ESSyntaxError('Invalid escape sequence')
            digits.append(char)
            self.advance()
        return unichr(int(u''.join(digits), 16))

    def parse_atom_escape(self):
        char = self.peek()
        if char != u'\\':
            raise ESSyntaxError('Invalid atom escape')
        self.advance()
        char = self.peek()
        if char in DECIMAL_DIGITS:
            self.advance()
            # TODO: Is this all that needs to be done here?
            if char == u'0' and self.peek() not in DECIMAL_DIGITS:
                return u'\0'
            return u'\\' + char
        elif char in CONTROL_CLASS_CHARS or char in CONTROL_ESCAPE_CHARS:
            self.advance()
            return u'\\' + char
        elif char == u'x':
            self.advance()
            return self.parse_hex_digits(2)
        elif char == u'u':
            self.advance()
            return self.parse_hex_digits(4)
        elif char == u'c':
            self.advance()
            lookahead = self.peek()
            if lookahead in CONTROL_LETTERS:
                self.advance()
                i = ord(lookahead)
                return unichr(i % 32)
        else:
            self.advance()
        return u'\\' + char

    def parse(self):
        parts = []
        while self.pos < len(self.string):
            char = self.peek()
            # TODO: Do we need to consider things differently in ranges?
            if char == '\\':
                parts.append(self.parse_atom_escape())
            else:
                parts.append(char)
                self.advance()
        return u''.join(parts)
