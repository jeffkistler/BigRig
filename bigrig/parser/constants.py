"""
Constants useful for lexing and parsing ECMAScript 3 source.
"""
HEX_DIGITS = frozenset(u"0123456789abcdefABCDEF")
DECIMAL_DIGITS = frozenset(u"0123456789")
LITERALS = frozenset(u"!.:;?=,(){}[]~!%/*-+><&^")
RESERVED_NAMES = frozenset(
    u"abstract enum int short boolean export interface static byte extends long "
    "super char final native synchronized class float package throws const goto "
    "private transient debugger implements protected volatile double import public".split()
)
KEYWORDS = frozenset(
    u"break else new var case finally return void catch for switch while "
    "continue function this with default if throw delete in try do instanceof "
    "typeof".split()
)
EOF_CHAR = u''
ESCAPE = u'\\'
SINGLE_ESCAPE_CHARS = frozenset(u'\'"\\bfnrtv')
