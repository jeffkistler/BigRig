#
# Token Types
#

INVALID = intern('INVALID')
EOF = intern('EOF')
EOL = intern('EOL')
RETURN = intern('RETURN')
BITOR = intern('BITOR')
BITXOR = intern('BITXOR')
BITAND = intern('BITAND')
EQ = intern('EQ')
NE = intern('NE')
LT = intern('LT')
LE = intern('LE')
GT = intern('GT')
GE = intern('GE')
LSH = intern('LSH') # <<
RSH = intern('RSH') # >>
ADD = intern('ADD')
SUB = intern('SUB')
MUL = intern('MUL')
DIV = intern('DIV')
MOD = intern('MOD')
NOT = intern('NOT')
BITNOT = intern('BITNOT')
NEW = intern('NEW')
DELETE = intern('DELETE')
TYPEOF = intern('TYPEOF')
STRING = intern('STRING')
NULL = intern('NULL')
THIS = intern('THIS')
FALSE = intern('FALSE')
TRUE = intern('TRUE')
SHEQ = intern('SHEQ') # ===
SHNE = intern('SHNE') # !==
REGEXP = intern('REGEXP')
THROW = intern('THROW')
IN = intern('IN')
INSTANCEOF = intern('INSTANCEOF')
TRY = intern('TRY')
LEFT_BRACKET = intern('LEFT_BRACKET') # [
RIGHT_BRACKET = intern('RIGHT_BRACKET') # ]
LEFT_CURLY_BRACE = intern('LEFT_CURLY_BRACE') # {
RIGHT_CURLY_BRACE = intern('RIGHT_CURLY_BRACE') # }
LEFT_PAREN = intern('LEFT_PAREN') # (
RIGHT_PAREN = intern('RIGHT_PAREN') # )
COMMA = intern('COMMA')
ASSIGN = intern('ASSIGN') # =
ASSIGN_BITOR = intern('ASSIGN_BITOR') # |=
ASSIGN_BITXOR = intern('ASSIGN_BITXOR') # ^=
ASSIGN_BITAND = intern('ASSIGN_BITAND') # &=
ASSIGN_LSH = intern('ASSIGN_LSH') # <<=
ASSIGN_RSH = intern('ASSIGN_RSH') # >>=
ASSIGN_URSH = intern('ASSIGN_URSH') # >>>=
ASSIGN_ADD = intern('ASSIGN_ADD') # +=
ASSIGN_SUB = intern('ASSIGN_SUB') # -=
ASSIGN_MUL = intern('ASSIGN_MUL') # *=
ASSIGN_DIV = intern('ASSIGN_DIV') # /=
ASSIGN_MOD = intern('ASSIGN_MOD') # %=
HOOK = intern('HOOK') # ?:
COLON = intern('COLON')
OR = intern('OR') # ||
AND = intern('AND') # &&
INC = intern('INC') # ++
DEC = intern('DEC') # --
DOT = intern('DOT')
FUNCTION = intern('FUNCTION')
IF = intern('IF')
ELSE = intern('ELSE')
SWITCH = intern('SWITCH')
CASE = intern('CASE')
DEFAULT = intern('DEFAULT')
WHILE = intern('WHILE')
DO = intern('DO')
FOR = intern('FOR')
BREAK = intern('BREAK')
CONTINUE = intern('CONTINUE')
VAR = intern('VAR')
WITH = intern('WITH')
CATCH = intern('CATCH')
RESERVED = intern('RESERVED')
IDENTIFIER = intern('IDENTIFIER')
SPACE = intern('SPACE')
COMMENT = intern('COMMENT')
SEMICOLON = intern('SEMICOLON')
FINALLY = intern('FINALLY')
VOID = intern('VOID')
DECIMAL = intern('DECIMAL')
INTEGER = intern('INTEGER')
URSH = intern('URSH') # >>>
SPACE = intern('SPACE')
LINETERM = intern('LINETERM')

#
# Useful mappings
#

LITERAL_TO_TYPE = {
    ".": DOT,
    ":": COLON,
    ";": SEMICOLON,
    "?": HOOK,
    "=": ASSIGN,
    ",": COMMA,
    "(": LEFT_PAREN,
    ")": RIGHT_PAREN,
    "{": LEFT_CURLY_BRACE,
    "}": RIGHT_CURLY_BRACE,
    "[": LEFT_BRACKET,
    "]": RIGHT_BRACKET,
    "~": BITNOT,
    "&": BITOR,
    "^": BITXOR,
    "!": NOT,
    "%": MOD,
    "/": DIV,
    "*": MUL,
    "-": SUB,
    "+": ADD,
    ">": GT,
    "<": LT,
}

KEYWORD_TO_TYPE = {
    "true": TRUE,
    "false": FALSE,
    "null": NULL,
    "break": BREAK,
    "else": ELSE,
    "new": NEW,
    "var": VAR,
    "case": CASE,
    "finally": FINALLY,
    "return": RETURN,
    "void": VOID,
    "catch": CATCH,
    "for": FOR,
    "switch": SWITCH,
    "while": WHILE,
    "continue": CONTINUE,
    "function": FUNCTION,
    "this": THIS,
    "with": WITH,
    "default": DEFAULT,
    "if": IF,
    "throw": THROW,
    "delete": DELETE,
    "in": IN,
    "try": TRY,
    "do": DO,
    "instanceof": INSTANCEOF,
    "typeof": TYPEOF,
}

PRECEDENCE = {
    # Punctuators
    EOF: 0,
    LEFT_PAREN: 0,
    RIGHT_PAREN: 0,
    LEFT_BRACKET: 0,
    RIGHT_BRACKET: 0,
    LEFT_CURLY_BRACE: 0,
    RIGHT_CURLY_BRACE: 0,
    COLON: 0,
    SEMICOLON: 0,
    DOT: 0,
    HOOK: 0,
    INC: 0,
    DEC: 0,
    # Assignment
    ASSIGN: 2,
    ASSIGN_BITOR: 2,
    ASSIGN_BITXOR: 2,
    ASSIGN_BITAND: 2,
    ASSIGN_LSH: 2,
    ASSIGN_RSH: 2,
    ASSIGN_URSH: 2,
    ASSIGN_ADD: 2,
    ASSIGN_SUB: 2,
    ASSIGN_MUL: 2,
    ASSIGN_DIV: 2,
    ASSIGN_MOD: 2,
    # Binary Operators
    COMMA: 1,
    OR: 4,
    AND: 5,
    BITOR: 6,
    BITXOR: 7,
    BITAND: 8,
    LSH: 11,
    RSH: 11,
    URSH: 11,
    ADD: 12,
    SUB: 12,
    MUL: 13,
    DIV: 13,
    MOD: 13,
    # Comparison Operators
    EQ: 9,
    NE: 9,
    SHEQ: 9,
    SHNE: 9,
    LT: 10,
    GT: 10,
    LE: 10,
    GE: 10,
    INSTANCEOF: 10,
    IN: 10,
}

#
# Token type classes
#

UNARY_OPS = frozenset((
    DELETE, VOID, TYPEOF, INC, DEC, ADD, SUB, BITNOT, NOT
))

COMPARISON_OPS = frozenset((
    EQ, NE, SHEQ, SHNE, LT, GT, LE, GE, INSTANCEOF, IN
))

ASSIGNMENT_OPS = frozenset((
    ASSIGN, ASSIGN_BITOR, ASSIGN_BITXOR, ASSIGN_BITAND, ASSIGN_LSH,
    ASSIGN_RSH, ASSIGN_URSH, ASSIGN_ADD, ASSIGN_SUB, ASSIGN_MUL,
    ASSIGN_DIV, ASSIGN_MOD
))

COUNT_OPS = frozenset((
    INC, DEC
))

#
# Token class
#

class Token(object):
    """
    A lexical unit in a source file.
    """
    __slots__ = ('type', 'value', 'locator')
    def __init__(self, type, value, locator=None):
        self.type = type
        self.value = value
        self.locator = locator
    
    def __str__(self):
        return self.type

    def __repr__(self):
        return '<Token %s>' % self
