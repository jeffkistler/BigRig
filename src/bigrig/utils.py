# import unicodedata as ud
import unicodedata


def categorize(c):
    try:
        cat = unicodedata.category(c)
    except ValueError:
        print "Saw '%s', code '%d'"
        raise
    return cat

class UD(object):
    def category(self, c):
        return categorize(c)
ud = UD()

    

#
# Character class checkers
#

IDENTIFIER_START_CHARS = frozenset((u'$', u'_'))
IDENTIFIER_START_CLASSES = frozenset(('Lu', 'Ll', 'Lt', 'Lm', 'Lo', 'Nl'))
IDENTIFIER_PART_CLASSES = frozenset(('Mn', 'Mc', 'Nd', 'Pc','Lu', 'Ll', 'Lt', 'Lm', 'Lo', 'Nl'))
WHITESPACE_CHARS = frozenset((u'\u0009', u'\u000b', u'\u000c', u'\u0020', u'\u00a0'))
LINE_TERMINATOR_CHARS = frozenset((u'\u000a', u'\u000d', u'\u2028', u'\u2029'))

def is_identifier_start(char):
    return char in IDENTIFIER_START_CHARS or ud.category(char) in IDENTIFIER_START_CLASSES

def is_identifier_part(char):
    return char in IDENTIFIER_START_CHARS or ud.category(char) in IDENTIFIER_PART_CLASSES
    
def is_whitespace_char(char):
    if len(char) != 1:
        print "WTF", char, len(char), type(char), ord(char)
    return char in WHITESPACE_CHARS or ud.category(char) == 'Zs'

def is_line_terminator(char):
    return char in LINE_TERMINATOR_CHARS

#
# Utility classes
#

class Locator(object):
    """
    Contains source location tracking information.
    """
    __slots__ = ('filename', 'line', 'column', 'offset')
    def __init__(self, filename, line, column, offset):
        self.filename = filename
        self.line = line
        self.column = column
        self.offset = offset

    def __repr__(self):
        return '<%s line %d, column %d>' % (self.filename, self.line, self.column)

class Stream(object):
    """
    A light wrapper on a codecs.Reader object that provides position tracking
    and a peek method.
    """
    def __init__(self, stream, offset=0):
        self.stream = stream
        self.offset = offset
        self.next_char = None
        self.next()

    def peek(self):
        return self.next_char

    def next(self):
        char = self.next_char
        self.next_char = self.stream.read(chars=1)
        return char

