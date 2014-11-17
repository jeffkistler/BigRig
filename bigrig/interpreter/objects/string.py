"""
Specification objects for the ``String`` built-in.
"""
from . import PropertyDescriptor, is_callable
from .base import ObjectInstance, FunctionInstance
from .function import define_native_method
from ..types import (
    StringType, ObjectType, Undefined, NaN, Null,
    get_primitive_type, get_arguments, check_object_coercible
)
from ..exceptions import ESTypeError


class StringInstance(ObjectInstance, StringType):
    """
    The specialized ``String`` object class.

    15.5.5
    """
    es_class = 'String'

    def __init__(self, interpreter, primitive_value):
        super(StringInstance, self).__init__(interpreter)
        self.primitive_value = primitive_value

    def get_own_property(self, name):
        """
        Specialized internal ``GetOwnProperty`` behavior implementation.

        15.5.5.2
        """
        desc = super(StringInstance, self).get_own_property(name)
        if desc is not Undefined:
            return desc
        name_int = self.interpreter.to_integer(name)
        s = self.interpreter.to_string(abs(name_int))
        if s != name:
            return Undefined
        if name_int >= len(self.primitive_value):
            return Undefined
        result = self.primitive_value[name_int]
        desc = PropertyDescriptor(
            value=result, enumerable=True, writable=False
        )
        return desc


class StringConstructor(FunctionInstance):
    """
    The ``String`` constructor function.
    """
    def __init__(self, interpreter):
        super(StringConstructor, self).__init__(interpreter)
        self.prototype = interpreter.FunctionPrototype
        define_native_method(self, 'fromCharCode', self.from_char_code_method, 1)
        self.set_property('length', 1)

    #
    # Internal method implementations
    #

    def call(self, this, arguments):
        """
        15.5.1.1
        """
        arg = arguments and arguments[0] or ""
        return self.interpreter.to_string(arg)

    def construct(self, arguments):
        """
        15.5.1.2
        """
        string_value = self.call(None, arguments)
        obj = StringInstance(self.interpreter, string_value)
        obj.set_property("length", len(string_value))
        obj.prototype = self.interpreter.StringPrototype
        obj.extensible = True
        return obj

    #
    # Method property implementations
    #

    def from_char_code_method(self, this, arguments):
        """
        ``String.fromCharCode`` method implementation.

        15.5.3.2
        """
        to_uint16 = self.interpreter.to_uint16
        char = lambda x: unichr(to_uint16(x))
        return u''.join(char(arg) for arg in arguments)


class StringPrototype(StringInstance):
    """
    The protototype object assigned to ``String`` instances.

    15.5.4
    """
    def __init__(self, interpreter):
        super(StringPrototype, self).__init__(interpreter, u'')
        self.prototype = interpreter.ObjectPrototype
        define_native_method(self, 'toString', self.to_string_method)
        define_native_method(self, 'valueOf', self.value_of_method)
        define_native_method(self, 'charAt', self.char_at_method, 1)
        define_native_method(self, 'charCodeAt', self.char_code_at_method, 1)
        define_native_method(self, 'concat', self.concat_method, 1)
        define_native_method(self, 'indexOf', self.index_of_method, 1)
        define_native_method(self, 'lastIndexOf', self.last_index_of_method, 1)
        define_native_method(self, 'localeCompare', self.locale_compare_method, 1)
        define_native_method(self, 'match', self.match_method, 1)
        define_native_method(self, 'replace', self.replace_method, 2)
        define_native_method(self, 'search', self.search_method, 1)
        define_native_method(self, 'slice', self.slice_method, 2)
        define_native_method(self, 'split', self.split_method, 2)
        define_native_method(self, 'substring', self.substring_method, 1)
        define_native_method(self, 'toLowerCase', self.to_lower_case_method)
        define_native_method(self, 'toLocaleLowerCase', self.to_locale_lower_case_method)
        define_native_method(self, 'toUpperCase', self.to_upper_case_method)
        define_native_method(self, 'toLocaleUpperCase', self.to_locale_upper_case_method)
        define_native_method(self, 'trim', self.trim_method)

    #
    # Internal methods
    #

    def is_regexp(self, obj):
        """
        """
        return get_primitive_type(obj) is ObjectType and obj.es_class == 'RegExp'

    def replace_value(self, replace_string, arguments):
        """
        """
        replace_string_len = len(replace_string)
        match = arguments[0]
        match_len = len(match)
        groups = arguments[1:-2]
        num_groups = len(groups)
        offset = arguments[-2]
        string = arguments[-1]
        parts = []
        index = 0
        next_index = replace_string.find('$', index)
        while next_index != -1:
            parts.append(replace_string[index:next_index])
            index = next_index + 1
            incr = 1
            if replace_string[index] == '$':
                parts.append('$')
            elif replace_string[index] == '&':
                parts.append(match)
            elif replace_string[index] == '`':
                parts.append(string[0:offset])
            elif replace_string[index] == '\'':
                parts.append(string[(offset+len(match)):])
            elif replace_string[index] in '0123456789':
                num = replace_string[index]
                if index + 1 < replace_string_len and replace_string[index+1] in '0123456789':
                    incr = 2
                    num = num + replace_string[index+1]
                num = int(num)
                if num > num_groups:
                    replace = ''
                else:
                    replace = groups[num - 1] #?
                parts.append(replace)
            index = index + incr
            next_index = replace_string.find('$', index)
        parts.append(replace_string[index:])
        return u''.join(parts)


    def split_match(self, string, q, separator):
        """
        Returns a ``MatchResult`` like ``RegExp.match`` given a string separator.
        """
        separator_length = len(separator)
        string_length = len(string)
        if (q + separator_length) > string_length:
            return None
        for i in range(separator_length):
            if string[q+i] != separator[i]:
                return None
        return (q+separator_length, [])

    #
    # Method property implementations
    #

    def to_string_method(self, this, arguments):
        """
        ``String.prototype.toString`` method implementation.

        15.5.4.2
        """
        if get_primitive_type(this) is not StringType:
            raise ESTypeError('String.prototype.toString called on invalid object')
        return self.interpreter.to_string(this)

    def value_of_method(self, this, arguments):
        """
        ``String.prototype.valueOf`` method implementation.

        15.5.4.3
        """
        if get_primitive_type(this) is not StringType:
            raise ESTypeError('String.prototype.valueOf called on invalid object')
        return self.interpreter.to_string(this)

    def char_at_method(self, this, arguments):
        """
        ``String.prototype.charAt`` method implementation.

        15.5.4.4
        """
        check_object_coercible(this)
        s = self.interpreter.to_string(this)
        pos = get_arguments(arguments, count=1)
        pos = self.interpreter.to_integer(pos)
        size = len(s)
        if pos < 0 or pos >= size:
            return u''
        return s[pos]

    def char_code_at_method(self, this, arguments):
        """
        ``String.prototype.charCodeAt`` method implementation.

        15.5.4.5
        """
        check_object_coercible(this)
        s = self.interpreter.to_string(this)
        pos = get_arguments(arguments, count=1)
        pos = self.interpreter.to_integer(pos)
        size = len(s)
        if pos < 0 or pos >= size:
            return NaN
        return ord(s[pos])

    def concat_method(self, this, arguments):
        """
        ``String.prototype.`` method implementation.

        15.5.4.6
        """
        check_object_coercible(this)
        to_string = self.interpreter.to_string
        values = [to_string(this)] + [to_string(arg) for arg in arguments]
        return u''.join(values)

    def index_of_method(self, this, arguments):
        """
        ``String.prototype.indexOf`` method implementation.

        15.5.4.7
        """
        check_object_coercible(this)
        to_string = self.interpreter.to_string
        s = to_string(this)
        search_str, pos = get_arguments(arguments, count=2)
        search_str = to_string(search_str)
        pos = self.interpreter.to_integer(pos)
        start = min(max(pos, 0), len(s))
        return s.find(search_str, start)

    def last_index_of_method(self, this, arguments):
        """
        ``String.prototype.lastIndexOf`` method implementation.

        15.5.4.8
        """
        check_object_coercible(this)
        to_string = self.interpreter.to_string
        s = to_string(this)
        search_str, pos = get_arguments(arguments, count=2)
        search_str = to_string(arguments[0])
        pos = self.interpreter.to_integer(pos)
        start = min(max(pos, 0), slen)
        return s.rfind(search_str, start)

    def locale_compare_method(self, this, arguments):
        """
        ``String.prototype.localeCompare`` method implementation.

        15.5.4.9
        """
        check_object_coercible(this)
        to_string = self.interpreter.to_string
        s = to_string(this)
        that = u''
        if len(arguments) > 0:
            that = to_string(arguments[0])
        return s == that

    def match_method(self, this, arguments):
        """
        ``String.prototype.match`` method implementation.

        15.5.4.10
        """
        check_object_coercible(this)
        s = self.interpreter.to_string(this)
        if len(arguments) > 0:
            regexp = arguments[0]
        else:
            return [u'']
        if not self.is_regexp(regexp):
            regexp = self.interpreter.RegExpConstructor.construct([regexp])
        re_exec = self.interpreter.RegExpPrototype.get('exec')
        if not regexp.get('global'):
            return re_exec.call(regexp, [s])
        regexp.put('lastIndex', 0)
        array = self.interpreter.ArrayConstructor.construct([])
        previous_last_index = 0
        lastmatch = True
        n = 0
        while lastmatch:
            result = re_exec.call(regexp, [s])
            if result is Null:
                lastmatch = False
            else:
                this_index = regexp.get('lastIndex')
                if this_index == previous_last_index:
                    regexp.put('lastIndex', this_index + 1)
                    previous_last_index = this_index + 1
                else:
                    previous_last_index = this_index
                match_str = result.get('0')
                desc = PropertyDescriptor(
                    value=match_str, writable=True, enumerable=True, configurable=True
                )
                array.define_own_property(unicode(n), desc, False)
                n = n + 1
        if n == 0:
            return Null
        return array


    def replace_method(self, this, arguments):
        """
        ``String.prototype.replace`` method implementation.

        15.5.4.11
        """
        check_object_coercible(this)
        string = self.interpreter.to_string(this)

        search_value, replace_value = get_arguments(arguments, count=2)

        if not is_callable(replace_value):
            replace_func = lambda this, args: self.replace_value(replace_value, args)
        else:
            replace_func = replace_value.call

        if self.is_regexp(search_value):
            if search_value.get('global') is not True:
                for i in range(len(string)):
                    match = search_value.match(string[i:], i)
                    if match is not None:
                        break
                if match is not None:
                    end, captures = match
                    arguments = [string[i:end]] + list(captures) + [i, string]
                    replace_string = replace_func(Undefined, arguments)
                    replace_string = self.interpreter.to_string(replace_string)
                    parts = [string[:i], replace_string, string[end:]]
                    return u''.join(parts)
                return string
            else:
                parts = []
                i = 0
                search_value.put('lastIndex', 0)
                last_end = i
                while not (i < 0 or i >= len(string)):
                    match = search_value.match(string, i)
                    if match is not None:
                        parts.append(string[last_end:i])
                        e, captures = match
                        arguments = [string[i:e]] + list(captures) + [i, string]
                        replace_string = replace_func(Undefined, arguments)
                        replace_string = self.interpreter.to_string(replace_string)
                        parts.append(replace_string)
                        i = last_end = e
                        search_value.put('lastIndex', last_end)
                    else:
                        i = i + 1
                parts.append(string[last_end:len(string)])
                return u''.join(parts)
        else:
            search_value = self.interpreter.to_string(search_value)
            match_index = self.index_of_method(string, [search_value])
            if match_index == -1:
                return string
            end = match_index + len(search_value)
            arguments = [search_value, match_index, string]
            # Bug 97 - Use Undefined as this value
            replace_string = replace_func(Undefined, arguments)
            replace_string = self.interpreter.to_string(replace_string)
            parts = [string[0:match_index], replace_string, string[end:]]
            return u''.join(parts)

    def search_method(self, this, arguments):
        """
        ``String.prototype.search`` method implementation.

        15.5.4.12
        """
        check_object_coercible(this)
        s = self.interpreter.to_string(this)
        if len(arguments) > 0:
            regexp = arguments[0]
        else:
            return 0
        if not self.is_regexp(regexp):
            regexp = self.interpreter.RegExpConstructor.construct([regexp])
        i = 0
        match = None
        while i < len(s) and match is None:
            match = regexp.match(s, i)
            if match:
                break
            i = i + 1
        if match is None:
            return -1
        return i

    def slice_method(self, this, arguments):
        """
        ``String.prototype.slice`` method implementation.

        15.5.4.13
        """
        check_object_coercible(this)
        to_string = self.interpreter.to_string
        to_integer = self.interpreter.to_integer
        s = to_string(this)
        length = len(s)
        start, end = get_arguments(arguments, count=2)
        if start is Undefined:
            start = 0
        else:
            start = to_integer(start)
        if end is Undefined:
            end = length
        else:
            end = to_integer(end)
        if start < 0:
            from_index = max(length + start, 0)
        else:
            from_index = min(start, length)
        if end < 0:
            to_index = max(length + end, 0)
        else:
            to_index = min(end, length)
        return s[from_index:to_index]

    def split_method(self, this, arguments):
        """
        ``String.prototype.split`` method implementation.

        15.5.4.14
        """
        check_object_coercible(this)
        string = self.interpreter.to_string(this)
        array = self.interpreter.ArrayConstructor.construct([])

        def define_array_index(index, value):
            desc = PropertyDescriptor(
                value=value, writable=True, enumerable=True, configurable=True
            )
            array.define_own_property(unicode(index), desc, False)

        separator, limit = get_arguments(arguments, count=2)
        if separator is Undefined:
            define_array_index(0, string)
            return array
        if limit is Undefined:
            limit = 2 ** 32 - 1
        elif limit == 0:
            return array
        else:
            limit = self.interpreter.to_uint32(limit)
        if not self.is_regexp(separator):
            separator = self.interpreter.to_string(separator)
            split_match = self.split_match
        else:
            split_match = lambda S, q, R: R.match(S, q)
        array_length = 0
        pos = 0
        string_length = len(string)
        if string_length == 0:
            z = split_match(string, 0, separator)
            if z is not None:
                return array
            define_array_index(0, string)
            return array
        q = pos
        while q != string_length:
            match = split_match(string, q, separator)
            if match is None:
                q = q + 1
            else:
                match_end, captures = match
                if match_end == pos:
                    q = q + 1
                else:
                    define_array_index(array_length, string[pos:q])
                    array_length = array_length + 1
                    if array_length == limit:
                        return array
                    pos = match_end
                    for capture in captures:
                        if capture is None:
                            capture = Undefined
                        define_array_index(array_length, capture)
                        array_length = array_length + 1
                        if array_length == limit:
                            return array
                        q = pos
        define_array_index(array_length, string[pos:])
        return array

    def substring_method(self, this, arguments):
        """
        ``String.prototype.substring`` method implementation.

        15.5.4.15
        """
        check_object_coercible(this)
        to_string = self.interpreter.to_string
        to_integer = self.interpreter.to_integer
        s = to_string(this)
        length = len(s)
        start, end = get_arguments(arguments, count=2)
        start = to_integer(start)
        if end is Undefined:
            end = length
        else:
            end = to_integer(arguments[1])
        final_start = min(max(start, 0), length)
        final_end = min(max(end, 0), length)
        from_index = min(start, end)
        to_index = max(start, end)
        return s[from_index:to_index]

    def to_lower_case_method(self, this, arguments):
        """
        ``String.prototype.toLowerCase`` method implementation.

        15.5.4.16
        """
        check_object_coercible(this)
        to_string = self.interpreter.to_string
        s = to_string(this)
        return s.lower()

    def to_locale_lower_case_method(self, this, arguments):
        """
        ``String.prototype.toLocaleLowerCase`` method implementation.

        15.5.4.17
        """
        check_object_coercible(this)
        to_string = self.interpreter.to_string
        s = to_string(this)
        return s.lower()

    def to_upper_case_method(self, this, arguments):
        """
        ``String.prototype.toUpperCase`` method implementation.

        15.5.4.18
        """
        check_object_coercible(this)
        to_string = self.interpreter.to_string
        s = to_string(this)
        return s.upper()

    def to_locale_upper_case_method(self, this, arguments):
        """
        ``String.prototype.toLocaleUpperCase`` method implementation.

        15.5.4.19
        """
        check_object_coercible(this)
        to_string = self.interpreter.to_string
        s = to_string(this)
        return s.upper()

    def trim_method(self, this, arguments):
        """
        ``String.prototype.trim`` method implementation.

        15.5.4.20
        """
        check_object_coercible(this)
        to_string = self.interpreter.to_string
        s = to_string(this)
        return s.strip()
