"""
Exception types that may be raised by ECMAScript operations. These correspond
to the built-in error objects.
"""

class ESError(Exception):
    """
    Base ECMAScript error.
    """
    pass


class ESTypeError(ESError):
    """
    Invalid type.
    """
    pass


class ESSyntaxError(ESError):
    """
    Invalid syntax.
    """
    pass


class ESReferenceError(ESError):
    """
    Invalid reference.
    """
    pass


class ESRangeError(ESError):
    """
    Invalid range.
    """
    pass


class ESEvalError(ESError):
    """
    An error during a call to ``eval``.
    """
    pass


class ESURIError(ESError):
    """
    Invalid URI component.
    """
    pass


class WrappedError(ESError):
    """
    """
    def __init__(self, error):
        self.error = error
