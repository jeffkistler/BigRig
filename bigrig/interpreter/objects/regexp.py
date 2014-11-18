"""
Specification objects for the ``RegExp`` built-in.
"""
import re
from . import PropertyDescriptor
from .base import ObjectInstance, FunctionInstance
from .function import define_native_method
from ..types import Undefined, Null, ObjectType, get_arguments, get_primitive_type
from ..exceptions import ESTypeError, ESSyntaxError
from ..literals import RegExpParser


class RegExpInstance(ObjectInstance):
    """
    The specialized ``RegExp`` object class.

    15.10.7
    """
    es_class = 'RegExp'

    def __init__(self, interpreter, source=None, is_global=False,
                 is_ignore_case=False, is_multiline=False):
        super(RegExpInstance, self).__init__(interpreter)
        self.source = source
        self.is_global= is_global
        self.is_ignore_case = is_ignore_case
        self.is_multiline = is_multiline
        self.set_property("source", source)
        self.set_property("global", is_global)
        self.set_property("ignoreCase", is_ignore_case)
        self.set_property("multiline", is_multiline)
        self.set_property("lastIndex", 0, writable=True)

    def match(self, string, index):
        """
        Internal ``Match`` method implementation.

        8.6.2
        """
        # returns (endIndex, captures)
        flags = 0
        if self.is_ignore_case:
            flags |= re.IGNORECASE
        if self.is_multiline:
            flags |= re.MULTILINE
        translated = RegExpParser.parse_string(self.source)
        regexp = re.compile(translated, flags)
        match = regexp.match(string, index)
        if match is None:
            return None
        return (match.end(), match.groups())


class RegExpConstructor(FunctionInstance):
    """
    The ``RegExp`` constructor function.

    15.10.3 & 15.10.4
    """
    def __init__(self, interpreter):
        super(RegExpConstructor, self).__init__(interpreter)
        self.prototype = interpreter.FunctionPrototype

    #
    # Helpers
    #

    def is_regexp(self, obj):
        """
        Is the given object of the ``RegExp`` class?
        """
        return getattr(obj, 'es_class', False) == 'RegExp'

    def parse_flags(self, flags):
        """
        Parse the given flags string.
        """
        is_global = False
        is_ignore_case = False
        is_multiline = False
        for char in flags:
            if char == 'g':
                if is_global:
                    raise ESSyntaxError("Multiple occurrences of 'g' in flags: %s", flags)
                is_global = True
            elif char == 'i':
                if is_ignore_case:
                    raise ESSyntaxError("Multiple occurrences of 'i' in flags: %s", flags)
                is_ignore_case = True
            elif char == 'm':
                if is_multiline:
                    raise ESSyntaxError("Multiple occurrences of 'm' in flags: %s", flags)
                is_multiline = True
            else:
                raise ESSyntaxError("Invalid flag %s" % char)
        return (is_global, is_ignore_case, is_multiline)

    #
    # Internal method implementations
    #

    def call(self, this, arguments):
        """
        15.10.3.1
        """
        pattern, flags = get_arguments(arguments, count=2)
        if self.is_regexp(pattern) and flags is Undefined:
            return this
        return self.construct(arguments)

    def construct(self, arguments):
        """
        15.10.3.2
        """
        pattern, flags = get_arguments(arguments, count=2)
        if self.is_regexp(pattern):
            if flags is not Undefined:
                raise ESTypeError('Flags are invalid when constructing a RegExp from another')
            r = pattern
            pattern = r.source
            is_global = r.is_global
            is_ignore_case = r.is_ignore_case
            is_multiline = r.is_multiline
            obj = RegExpInstance(
                self.interpreter, pattern, is_global, is_ignore_case, is_multiline
            )
            obj.prototype = self.interpreter.RegExpPrototype
            obj.set_property("prototype", self.interpreter.RegExpPrototype)
            return obj
        elif pattern is Undefined:
            pattern = ''
        else:
            pattern = self.interpreter.to_string(pattern)
        if pattern == u'':
            pattern = u'(?:)'
        if flags is Undefined:
            flags = ''
        else:
            flags = self.interpreter.to_string(flags)
        # Validate
        is_global, is_ignore_case, is_multiline = self.parse_flags(flags)
        # Construct
        obj = RegExpInstance(
            self.interpreter, source=pattern, is_global=is_global,
            is_ignore_case=is_ignore_case, is_multiline=is_multiline
        )
        obj.prototype = self.interpreter.RegExpPrototype
        obj.set_property("prototype", self.interpreter.RegExpPrototype)
        return obj


class RegExpPrototype(RegExpInstance):
    """
    The prototype object assigned to ``RegExp`` instances.
    """
    def __init__(self, interpreter):
        super(RegExpPrototype, self).__init__(interpreter)
        self.prototype = interpreter.ObjectPrototype
        define_native_method(self, 'exec', self.exec_method)
        define_native_method(self, 'test', self.test_method)
        define_native_method(self, 'toString', self.to_string_method, 0)

    def exec_method(self, this, arguments):
        """
        ``RegExp.prototype.exec`` method implementation.

        15.10.6.2
        """
        if get_primitive_type(this) is not ObjectType or this.es_class != 'RegExp':
            raise ESTypeError('RegExp.prototype.execute is not generic')
        s = get_arguments(arguments, count=1)
        s = self.interpreter.to_string(s)
        length = len(s)
        i = self.interpreter.to_integer(this.get('lastIndex'))
        is_global = this.get('global')
        if is_global is False:
            i = 0
        match = None
        while True:
            if i < 0 or i > length:
                this.put('lastIndex', 0, True)
                return Null
            match = this.match(s, i)
            if match is not None:
                break
            i = i + 1
        e, captures = match
        if is_global:
            this.put('lastIndex', e, True)

        array = self.interpreter.ArrayConstructor.construct([])
        desc = PropertyDescriptor(
            value=i, writable=True, enumerable=True, configurable=True
        )
        array.define_own_property("index", desc, True)

        desc = PropertyDescriptor(
            value=s, writable=True, enumerable=True, configurable=True
        )
        array.define_own_property("input", desc, True)

        desc = PropertyDescriptor(
            value=len(captures) + 1
        )
        array.define_own_property("length", desc, True)

        desc = PropertyDescriptor(
            value=s[i:e], writable=True, enumerable=True, configurable=True
        )
        array.define_own_property('0', desc, True)
        for i, capture in enumerate(captures, 1):
            if capture is not None:
                desc = PropertyDescriptor(
                    value=capture, writable=True, enumerable=True, configurable=True
                )
                array.define_own_property(unicode(i), desc, True)
        return array

    def test_method(self, this, arguments):
        """
        ``RegExp.prototype.test`` method implementation.

        # 15.10.6.3
        """
        match = self.exec_method(this, arguments)
        if match is not Null:
            return True
        return False

    def to_string_method(self, this, arguments):
        """
        ``RegExp.prototype.toString`` method implementation.

        15.10.6.4
        """
        if not isinstance(this, ObjectType) or this.es_class != 'RegExp':
            raise ESTypeError('RegExp.prototype.toString is not generic')
        pattern = this.source
        flags = []
        if this.is_global:
            flags.append('g')
        if this.is_ignore_case:
            flags.append('i')
        if this.is_multiline:
            flags.append('m')
        flags = ''.join(flags)
        return u'/%s/%s' % (pattern, flags)
