"""
An ECMAScript 3 lexical scanner implementation and various related utilities.
"""
from bigrig.token import *
from bigrig.constants import *
from bigrig.utils import (
    is_identifier_start, is_identifier_part, is_whitespace_char,
    is_line_terminator, Locator, Stream
)

class Scanner(object):
    """
    Produces lexical tokens from a given input stream.
    """
    def __init__(self, stream, filename=None, line=0, column=0, offset=0):
        self.stream = Stream(stream, offset)
        self.filename = filename
        self.line = line
        self.column = column
        self.buffer = []
        self.locator = None

    #
    # Public interface
    #

    def next(self):
        """
        Get the next token from the stream.
        """
        return self.scan()

    #
    # Utilities
    #

    def make_locator(self):
        """
        Make a source position locator using the stored state.
        """
        return Locator(
            self.filename, self.line, self.column, self.stream.offset
        )

    def peek_char(self):
        """
        Have a look at the next character in the stream without advancing
        the position in it.
        """
        return self.stream.peek()

    def next_in(self, collection):
        """
        Look at the next character in the stream and check if it is in the
        given collection.
        """
        next = self.peek_char()
        return next != EOF_CHAR and next in collection

    def advance(self):
        """
        Move the state forward one character.

        Note that this sets up location tracking and increments the
        column count.
        """
        self.buffer.append(self.stream.next())
        self.column += 1
        if self.locator is None:
            self.locator = self.make_locator()

    def make_token(self, type):
        """
        Make a lexical token with the given type using the stored state.
        """
        value = u''.join(self.buffer)
        token = Token(type, value, self.locator)
        self.buffer = []
        self.locator = None
        return token

    def make_invalid_token(self):
        """
        A quick shortcut to produce an INVALID token when the peeked char is
        invalid in the current context.
        """
        self.advance()
        return self.make_token(INVALID)

    def is_whitespace_char(self, char):
        if char == EOF_CHAR:
            return False
        return is_whitespace_char(char)

    def is_line_terminator(self, char):
        if char == EOF_CHAR:
            return False
        return is_line_terminator(char)

    def is_identifier_start(self, char):
        if char == EOF_CHAR:
            return False
        return is_identifier_start(char)

    def is_identifier_part(self, char):
        if char == EOF_CHAR:
            return False
        return is_identifier_part(char)

    #
    # Scanning methods
    #

    def consume_whitespace(self):
        """
        Eat whitespace, not including line terminators.
        """
        next = self.peek_char()
        while self.is_whitespace_char(next):
            self.advance()
            next = self.peek_char()

    def scan_whitespace(self):
        """
        Scan whitespace from the stream.
        """
        self.consume_whitespace()
        return self.make_token(SPACE)

    def consume_line_terminators(self):
        """
        Eat line terminators, updating the file position state.
        """
        next = self.peek_char()
        while self.is_line_terminator(next):
            self.advance()
            if next == u'\r':
                peek = self.peek_char()
                if peek == u'\n':
                    self.advance()
            self.line += 1
            self.column = 0
            next = self.peek_char()

    def scan_line_terminators(self):
        """
        Scan line terminators from the stream.
        """
        self.consume_line_terminators()
        return self.make_token(LINETERM)

    def scan_single_line_comment(self):
        """
        Scan a single line comment from the stream.
        """
        while True:
            next = self.peek_char()
            if next == EOF_CHAR or self.is_line_terminator(next):
                break
            self.advance()
        return self.make_token(COMMENT)

    def scan_multiline_comment(self):
        """
        Scan a multiline comment from the stream.
        """
        while True:
            next = self.peek_char()
            if next == EOF_CHAR:
                return self.make_invalid_token()
            elif self.is_line_terminator(next):
                self.consume_line_terminators()
                continue
            elif next == u'*':
                self.advance()
                next = self.peek_char()
                if next == u'/':
                    self.advance()
                    break
                continue
            self.advance()
        return self.make_token(COMMENT)

    def scan_identifier_or_keyword(self):
        """
        Scan an identifier or keyword token from the stream.
        """
        next = self.peek_char()
        if next == ESCAPE:
            # Check buffer here to determine if invalid?
            self.consume_unicode_escape()
        elif not self.is_identifier_start(next):
            return self.make_invalid_token()
        else:
            self.advance()
        next = self.peek_char()
        while True:
            if next != EOF_CHAR and self.is_identifier_part(next):
                self.advance()
                next = self.peek_char()
                continue
            elif next == ESCAPE:
                # Check buffer here to determine if invalid?
                self.consume_unicode_escape()
                next = self.peek_char()
            else:
                break
        # Check the value to see if we have a reserved name or keyword
        value = u''.join(self.buffer)
        if value in KEYWORD_TO_TYPE:
            return self.make_token(KEYWORD_TO_TYPE[value])
        elif value in RESERVED_NAMES:
            return self.make_token(RESERVED)
        return self.make_token(IDENTIFIER)

    def consume_decimal_digits(self):
        """
        Consume while the next character is a decimal digit.
        """
        while self.next_in(DECIMAL_DIGITS):
            self.advance()

    def consume_hex_digits(self, length=2):
        """
        Consume hexadecimal digits up to a given length.
        """
        for i in xrange(length):
            if not self.next_in(HEX_DIGITS):
                # Error
                break
            self.advance()

    def scan_number(self, decimal=False):
        """
        Scan a decimal or integer literal token from the stream.
        """
        type = decimal and DECIMAL or INTEGER
        next = self.peek_char()
        if next == EOF_CHAR:
            return
        elif next == u'0': # Possible HexIntegerLiteral
            self.advance()
            if self.next_in(u'xX'):
                self.advance()
                while self.next_in(HEX_DIGITS):
                    self.advance()
                return self.make_token(INTEGER)
        self.consume_decimal_digits()
        next = self.peek_char()
        if next == u'.':
            if decimal:
                return self.make_token(DECIMAL)
            self.advance()
            type = DECIMAL
        self.consume_decimal_digits()
        # Scan exponent
        # Should this always be DECIMAL?
        if self.next_in(u'eE'):
            self.advance()
            if self.next_in(u'-+'):
                if next == u'-':
                    type = DECIMAL
                self.advance()
            self.consume_decimal_digits()
        return self.make_token(type)

    def scan_string(self):
        """
        Scan a string literal token from the stream.
        """
        quote = self.peek_char()
        self.advance()
        while True:
            next = self.peek_char()
            if next == EOF_CHAR or self.is_line_terminator(next):
                return self.make_invalid_token()
            elif next == quote:
                self.advance()
                break
            elif next == ESCAPE:
                self.consume_escape()
            else:
                self.advance()
        return self.make_token(STRING)

    def consume_unicode_escape(self):
        """
        Scan a full unicode escape sequence: \uXXXX.
        """
        next = self.peek_char()
        if next != ESCAPE:
            return
        self.advance()
        next = self.peek_char()
        if next != u'u':
            return
        self.advance()
        self.consume_hex_digits(length=4)

    def consume_escape(self):
        """
        Scan an escape sequence in a string.
        """
        next = self.peek_char()
        if next != ESCAPE:
            # Error
            return
        self.advance()
        next = self.peek_char()
        if next == EOF_CHAR:
            # Error
            return
        if next == u'x':
            self.advance()
            self.consume_hex_digits()
        elif next == u'u':
            self.advance()
            self.consume_hex_digits(4)
        elif next in SINGLE_ESCAPE_CHARS:
            self.advance()
        else: # SourceCharacter?
            self.advance()
        return

    def scan_regexp(self):
        """
        Scan a regular expression literal token from the stream.

        Note that this is parse-context sensitive, so it must be called from
        the parser itself.
        """
        # The first char must not make a possible comment token
        # this will never happen, we hope, but check anyway.
        if self.next_in(u'*/'):
            return self.make_invalid_token()
        in_character_class = False
        while True:
            next = self.peek_char()
            if next == EOF_CHAR or self.is_line_terminator(next):
                return self.make_invalid_token()
            elif next == u'[':
                in_character_class = True
            elif next == u']':
                in_character_class = False
            elif next == ESCAPE:
                # Any character except line terminator allowed after a backslash
                self.advance()
                next = self.peek_char()
                if next == EOF_CHAR or self.is_line_terminator(next):
                    return self.make_invalid_token()
            elif next == u'/' and not in_character_class:
                self.advance()
                break
            self.advance()
        return self.make_token(REGEXP)

    def scan_regexp_flags(self):
        """
        Scan the flags token for a regular expression literal from the stream.
        """
        # Only IdentifierPart here
        next = self.peek_char()
        while next != EOF_CHAR and self.is_identifier_part(next):
            if next == ESCAPE:
                self.consume_unicode_escape()
            else:
                self.advance()
            next = self.peek_char()
        return self.make_token(IDENTIFIER)

    def scan(self):
        """
        Produce the next token from the input stream.
        """
        self.locator = None
        next = self.peek_char()
        if next == EOF_CHAR:
            # Not sure we actually care about storing a value and location
            # for the end of the file, but here it goes anyway
            # Note that this will continue incrementing the column upon
            # successive calls.
            self.advance() 
            return self.make_token(EOF)
        elif self.is_whitespace_char(next):
            return self.scan_whitespace()
        elif self.is_line_terminator(next):
            return self.scan_line_terminators()
        elif self.is_identifier_start(next) or next == ESCAPE:
            return self.scan_identifier_or_keyword()
        elif next in u'\'"':
            return self.scan_string()
        elif next == u'.':
            self.advance()
            if self.next_in(DECIMAL_DIGITS):
                return self.scan_number(decimal=True)
            return self.make_token(DOT)
        elif next in DECIMAL_DIGITS:
            return self.scan_number()
        elif next == u'/':
            self.advance()
            next = self.peek_char()
            if next == u'/':
                return self.scan_single_line_comment()
            elif next == u'*':
                return self.scan_multiline_comment()
            elif next == u'=':
                self.advance()
                return self.make_token(ASSIGN_DIV)
            return self.make_token(DIV)
        elif next == u'=':
            # ASSIGN, EQ, SHEQ
            self.advance()
            next = self.peek_char()
            if next == u'=':
                self.advance()
                next = self.peek_char()
                if next == u'=':
                    self.advance()
                    return self.make_token(SHEQ)
                return self.make_token(EQ)
            return self.make_token(ASSIGN)
        elif next == u'!':
            # NOT, NE, SHNE
            self.advance()
            next = self.peek_char()
            if next == u'=':
                self.advance()
                next = self.peek_char()
                if next == u'=':
                    self.advance()
                    return self.make_token(SHNE)
                return self.make_token(NE)
            return self.make_token(NOT)
        elif next == u'+':
            # NUMBER, ADD, INC, ASSIGN_ADD
            self.advance()
            next = self.peek_char()
            if next == u'=':
                self.advance()
                return self.make_token(ASSIGN_ADD)
            elif next == u'+':
                self.advance()
                return self.make_token(INC)
            return self.make_token(ADD)
        elif next == u'-':
            # NUMBER, SUB, DEC, ASSIGN_SUB
            self.advance()
            next = self.peek_char()
            if next == u'=':
                self.advance()
                return self.make_token(ASSIGN_SUB)
            elif next == u'-':
                self.advance()
                return self.make_token(DEC)
            return self.make_token(SUB)
        elif next == u'&':
            # BITAND, AND, ASSIGN_BITAND
            self.advance()
            next = self.peek_char()
            if next == u'&':
                self.advance()
                return self.make_token(AND)
            elif next == u'=':
                self.advance()
                return self.make_token(ASSIGN_BITAND)
            return self.make_token(BITAND)
        elif next == u'|':
            # BITOR, OR, ASSIGN_BITOR
            self.advance()
            next = self.peek_char()
            if next == u'|':
                self.advance()
                return self.make_token(OR)
            elif next == u'=':
                self.advance()
                return self.make_token(ASSIGN_BITOR)
            return self.make_token(BITOR)
        elif next == u'*':
            # MUL, ASSIGN_MUL
            self.advance()
            next = self.peek_char()
            if next == u'=':
                self.advance()
                return self.make_token(ASSIGN_MUL)
            return self.make_token(MUL)
        elif next == u'<':
            # LE, LT, LSH, ASSIGN_LSH
            self.advance()
            next = self.peek_char()
            if next == u'=':
                self.advance()
                return self.make_token(LE)
            elif next == u'<':
                self.advance()
                next = self.peek_char()
                if next == u'=':
                    self.advance()
                    return self.make_token(ASSIGN_LSH)
                return self.make_token(LSH)
            return self.make_token(LT)
        elif next == u'>':
            # GE, GT, RSH, ASSIGN_RSH
            self.advance()
            next = self.peek_char()
            if next == u'=':
                self.advance()
                return self.make_token(GE)
            elif next == u'>':
                self.advance()
                next = self.peek_char()
                if next == u'=':
                    self.advance()
                    return self.make_token(ASSIGN_RSH)
                elif next == u'>':
                    self.advance()
                    if self.peek_char() == u'=':
                        self.advance()
                        return self.make_token(ASSIGN_URSH)
                    return self.make_token(URSH)
                return self.make_token(RSH)
            return self.make_token(GT)
        elif next == u'%':
            # MOD, ASSIGN_MOD
            self.advance()
            next = self.peek_char()
            if next == u'=':
                self.advance()
                return self.make_token(ASSIGN_MOD)
            return self.make_token(MOD)
        elif next == u'^':
            # BITXOR, ASSIGN_BITXOR
            self.advance()
            next = self.peek_char()
            if next == u'=':
                self.advance()
                return self.make_token(ASSIGN_BITXOR)
            return self.make_token(BITXOR)
        elif next in LITERAL_TO_TYPE:
            self.advance()
            return self.make_token(LITERAL_TO_TYPE[next])
        # Fallthrough case
        return self.make_invalid_token()

class TokenStream(object):
    """
    A simple wrapper that does some state tracking to provide token lookahead.

    Note that since regular expression literals are parse context sensitive we
    provide an interface to perform scanning of them here.
    """
    def __init__(self, scanner):
        self.scanner = scanner
        self.next_token = None
        self.has_line_terminator_before_next = False
        self.next()

    def next(self):
        """
        Get the next token, keeping track of the lookahead and line terminators
        seen in the stream.
        """
        self.has_line_terminator_before_next = False
        token = self.next_token
        next = self.scanner.next()
        type = next.type
        while type != EOF and type in (SPACE, LINETERM, COMMENT):
            if type == LINETERM:
                self.has_line_terminator_before_next = True
            next = self.scanner.next()
            type = next.type
        self.next_token = next
        return token

    def peek(self):
        """
        Look at the next token without advancing the stream state.
        """
        return self.next_token

    def scan_regexp(self):
        """
        Must be called after ``peek`` returns a ``DIV`` or ``DIV_ASSIGN``
        token.
        """
        start_token = self.next_token
        token = self.scanner.scan_regexp()
        if token.type == REGEXP:
            locator = start_token.locator
            value = start_token.value
            value = value + token.value
            token = Token(REGEXP, value, locator)
        else:
            # Advance the scanner state upon invalid regex pattern.
            # This is probably pointless.
            self.next()
        return token

    def scan_regexp_flags(self):
        """
        Must be called after ``scan_regexp``.
        """
        token = self.scanner.scan_regexp_flags()
        if token.type == IDENTIFIER:
            # Advance the stream lookahead state to allow the parser
            # to continue functioning without the bookkeeping overhead.
            self.next()
        return token

class TokenStreamAllowReserved(TokenStream):
    """
    A stream that turns ``RESERVED`` tokens into ``IDENTIFIER`` tokens.
    """
    def coerce_reserved(self, token):
        if token is not None and token.type == RESERVED:
            return Token(IDENTIFIER, token.value, token.locator)
        return token

    def peek(self):
        token = super(TokenStreamAllowReserved, self).peek()
        return self.coerce_reserved(token)

    def next(self):
        token = super(TokenStreamAllowReserved, self).next()
        return self.coerce_reserved(token)

#
# Utilities
#

def make_file_scanner(fd, filename=None, line=0, column=0, encoding='utf-8'):
    """
    Build and return a scanner for the given file object.
    """
    import codecs
    Reader = codecs.getreader(encoding)
    stream = Reader(fd)
    return Scanner(stream, filename, line, column)

def make_string_scanner(string, filename=None, line=0, column=0, encoding='utf-8'):
    """
    Build and return a scanner for the given string object.
    """
    try:
        from cStringIO import StringIO
    except ImportError:
        from StringIO import StringIO
    return make_file_scanner(StringIO(string), filename, line, column, encoding)
