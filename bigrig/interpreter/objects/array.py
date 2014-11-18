"""
Specification objects for the ``Array`` built-in.
"""
from . import PropertyDescriptor, is_callable
from .base import ObjectInstance, FunctionInstance
from .function import define_native_method
from ..exceptions import ESTypeError, ESRangeError
from ..types import Undefined, Null, NumberType, ObjectType, get_arguments, get_primitive_type


class ArrayInstance(ObjectInstance):
    """
    The specialized ``Array`` object class.

    15.4.5
    """
    es_class = 'Array'
    def __init__(self, interpreter):
        super(ArrayInstance, self).__init__(interpreter)
        self.set_property('length', 0, writable=True)

    def define_own_property(self, name, desc, throw):
        """
        Override behavior for the ``length`` and array index ``name`` cases.

        15.4.5.1
        """
        # Aliases
        default = super(ArrayInstance, self).define_own_property
        i = self.interpreter
        to_string = i.to_string
        to_number = i.to_number
        to_uint32 = i.to_uint32

        # Utilities
        def is_array_index(p):
            return p == to_string(to_uint32(p))

        def reject():
            if throw:
                raise ESTypeError('Invalid property assignment %s' % name)
            return False

        # Actual logic
        old_len_desc = self.get_own_property('length')
        old_length = old_len_desc.value
        if name == 'length':
            if desc.value is None:
                return default(name, desc, throw)
            new_len_desc = PropertyDescriptor.clone(desc)
            new_len = to_uint32(desc.value)
            if new_len != to_number(desc.value):
                raise ESRangeError('Invalid length value %s' % to_number(desc.value))
            new_len_desc.value = new_len
            if new_len >= old_length:
                return default(name, new_len_desc, throw)
            if old_len_desc.writable is False:
                return reject()
            if new_len_desc.writable is None or new_len_desc.writable is True:
                new_writable = True
            else:
                new_writable = False
                new_len_desc.writable = True
            succeeded = default(name, new_len_desc, throw)
            if not succeeded:
                return False
            while new_len < old_length:
                old_length = old_length - 1
                delete_succeeded = self.delete(to_string(old_length), False)
                if not delete_succeeded:
                    new_len_desc.value = old_length + 1
                    if new_writable is False:
                        new_len_desc.writable = False
                        default(name, new_len_desc, False)
                        return reject()
            if new_writable is False:
                new_desc = PropertyDescriptor(writable=False)
                default(name, new_desc, False)
            return True
        elif is_array_index(name):
            index = to_uint32(name)
            if index >= old_length and old_len_desc.writable is False:
                return reject()
            succeeded = default(name, desc, False)
            if not succeeded:
                return reject()
            if index >= old_length:
                old_len_desc.value = index + 1
                return default('length', old_len_desc, False)
        else:
            return default(name, desc, throw)


class ArrayConstructor(FunctionInstance):
    """
    The ``Array`` constructor function.

    15.4.1 & 15.4.2
    """
    def __init__(self, interpreter):
        super(ArrayConstructor, self).__init__(interpreter)
        self.prototype = interpreter.FunctionPrototype
        define_native_method(self, 'isArray', self.is_array_method, 1)
        self.set_property('length', 1)

    #
    # Internal methods
    #

    def call(self, this, arguments):
        """
        Behaves the same way as if it were in a ``new`` expression.
        
        15.4.1.1
        """
        return self.construct(arguments)

    def construct(self, arguments):
        """
        Build and return the specialized ``Array`` object instance.

        15.4.2
        """
        obj = ArrayInstance(self.interpreter)
        obj.prototype = self.interpreter.ArrayPrototype
        num_args = len(arguments)
        if num_args == 1:
            length = arguments[0]
            is_number = get_primitive_type(length) is NumberType
            if is_number:
                uint_length = self.interpreter.to_uint32(length)
                if length == uint_length:
                    obj.set_property('length', length, writable=True)
                    return obj
                else:
                    raise ESRangeError('Invalid length value')
        obj.set_property('length', num_args, writable=True)
        for i, arg in enumerate(arguments):
            desc = PropertyDescriptor(
                value=arg, writable=True, enumerable=True, configurable=True
            )
            obj.define_own_property(unicode(i), desc, False)
        return obj

    #
    # Method property implementations
    #

    def is_array_method(self, this, arguments):
        """
        Built-in method that checks if the internal class of the given argument
        is ``Array``.

        15.4.3.2
        """
        arg = get_arguments(arguments, count=1)
        if get_primitive_type(arg) is not ObjectType:
            return False
        elif arg.es_class == 'Array':
            return True
        return False


class ArrayPrototype(ArrayInstance):
    """
    The prototype object assigned to ``Array`` instances.

    15.4.4
    """
    def __init__(self, interpreter):
        super(ArrayPrototype, self).__init__(interpreter)
        define_native_method(self, 'toString', self.to_string_method)
        define_native_method(self, 'toLocaleString', self.to_locale_string_method)
        define_native_method(self, 'concat', self.concat_method, 1)
        define_native_method(self, 'join', self.join_method, 1)
        define_native_method(self, 'pop', self.pop_method)
        define_native_method(self, 'push', self.push_method, 1)
        define_native_method(self, 'reverse', self.reverse_method)
        define_native_method(self, 'shift', self.shift_method)
        define_native_method(self, 'slice', self.slice_method, 2)
        define_native_method(self, 'sort', self.sort_method, 1)
        define_native_method(self, 'splice', self.splice_method, 2)
        define_native_method(self, 'unshift', self.unshift_method, 1)
        define_native_method(self, 'indexOf', self.index_of_method, 1)
        define_native_method(self, 'lastIndexOf', self.last_index_of_method, 1)
        define_native_method(self, 'every', self.every_method, 1)
        define_native_method(self, 'some', self.some_method, 1)
        define_native_method(self, 'forEach', self.for_each_method, 1)
        define_native_method(self, 'map', self.map_method, 1)
        define_native_method(self, 'filter', self.filter_method, 1)
        define_native_method(self, 'reduce', self.reduce_method, 1)
        define_native_method(self, 'reduceRight', self.reduce_right_method, 1)
        self.prototype = interpreter.ObjectPrototype

    def to_string_method(self, this, arguments):
        """
        ``Array.prototype.toString`` implementation.

        15.4.4.2
        """
        array = self.interpreter.to_object(this)
        func = array.get('join')
        if not is_callable(func):
            func = self.interpreter.ObjectPrototype.to_string
        return func.call(array, [])

    def to_locale_string_method(self, this, arguments):
        """
        ``Array.prototype.toLocaleString`` implementation.

        15.4.4.3
        """
        to_object = self.interpreter.to_object
        array = to_object(this)
        array_length = array.get('length')
        length = self.interpreter.to_uint32(array_length)
        separator = u','
        if not length:
            return u''
        elements = []
        for i in range(length):
            element = array.get(unicode(i))
            if element is Null or element is Undefined:
                elements.append(u'')
            element = to_object(element)
            func = element.get('toLocaleString')
            if not is_callable(func):
                raise ESTypeError('toLocaleString is not a function')
            elements.append(func.call(element, []))
        return separator.join(elements)

    def concat_method(self, this, arguments):
        """
        ``Array.prototype.concat`` implementation.

        15.4.4.4
        """
        o = self.interpreter.to_object(this)
        array = self.interpreter.ArrayConstructor.construct([])
        items = [o] + arguments
        index = 0
        for item in items:
            if getattr(item, 'es_class', None) == 'Array':
                length = item.get('length')
                for i in range(length):
                    p = unicode(i)
                    if item.has_property(p):
                        element = item.get(p)
                        desc = PropertyDescriptor(
                            value=element, writable=True, enumerable=True, configurable=True
                        )
                        array.define_own_property(unicode(index), desc, False)
                    index += 1
            else:
                desc = PropertyDescriptor(
                    value=item, writable=True, enumerable=True, configurable=True
                )
                array.define_own_property(unicode(index), desc, False)
                index += 1
        return array

    def join_method(self, this, arguments):
        """
        ``Array.prototype.join`` implementation.

        15.4.4.5
        """
        to_string = self.interpreter.to_string
        o = self.interpreter.to_object(this)
        separator = get_arguments(arguments, count=1)
        if separator is Undefined:
            separator = u','
        else:
            separator = to_string(separator)
        length = self.interpreter.to_uint32(o.get('length'))
        if length == 0:
            return u''
        strings = []
        for i in range(length):
            index = unicode(i)
            if o.has_property(index):
                element = o.get(index)
                if element is Undefined or element is Null:
                    element = ''
                else:
                    element = to_string(element)
                strings.append(element)
        return separator.join(strings)

    def pop_method(self, this, arguments):
        """
        ``Array.prototype.pop`` implementation.

        15.4.4.6
        """
        o = self.interpreter.to_object(this)
        length = self.interpreter.to_uint32(o.get('length'))
        if length > 0:
            index = unicode(length - 1)
            element = o.get(index)
            o.delete(index)
            o.put('length', int(index), True)
            return element
        return Undefined

    def push_method(self, this, arguments):
        """
        ``Array.prototype.push`` implementation.

        15.4.4.7
        """
        o = self.interpreter.to_object(this)
        num_args = len(arguments)
        length = self.interpreter.to_uint32(o.get('length'))
        new_length = length + num_args
        if arguments:
            for i, item in enumerate(arguments):
                o.put(unicode(length + i), item, True)
            o.put('length', new_length, True)
        return new_length

    def reverse_method(self, this, arguments):
        """
        ``Array.prototype.reverse`` implementation.

        15.4.4.8
        """
        o = self.interpreter.to_object(this)
        length = self.interpreter.to_uint32(o.get('length'))
        middle = length // 2
        for lower in range(0, middle):
            upper = length - lower - 1
            lower_index = unicode(lower)
            upper_index = unicode(upper)
            lower_exists = o.has_property(lower_index)
            upper_exists = o.has_property(upper_index)
            lower_val = lower_exists and o.get(lower_index)
            upper_val = upper_exists and o.get(upper_index)
            if lower_exists and upper_exists:
                o.put(lower_index, upper_val, True)
                o.put(upper_index, lower_val, True)
            elif upper_exists:
                o.put(lower_index, upper_val, True)
                o.delete(upper_index, True)
            elif lower_exists:
                o.put(upper_index, lower_val, True)
                o.delete(lower_index, True)
        return o

    def shift_method(self, this, arguments):
        """
        ``Array.prototype.shift`` implementation.

        15.4.4.9
        """
        o = self.interpreter.to_object(this)
        length = self.interpreter.to_uint32(o.get('length'))
        if length == 0:
            return Undefined
        first = o.get('0')
        for i in range(1, length):
            from_index = unicode(i)
            to_index = unicode(i - 1)
            if o.has_property(from_index):
                val = o.get(from_index)
                o.put(to_index, val, True)
            else:
                o.delete(to_index, True)
        o.delete(unicode(length - 1), True)
        before = o.get('length')
        o.put('length', length - 1, True)
        after = o.get('length')
        return first

    def slice_method(self, this, arguments):
        """
        ``Array.prototype.slice`` implementation.

        15.4.4.10
        """
        o = self.interpreter.to_object(this)
        length = self.interpreter.to_uint32(o.get('length'))
        start, end = get_arguments(arguments, count=2)
        start = self.interpreter.to_integer(start)
        if end is Undefined:
            end = length
        else:
            end = self.interpreter.to_integer(end)
        if start < 0:
            start = max(length + start, 0)
        else:
            start = min(start, length)
        if end < 0:
            end = max(length + end, 0)
        else:
            end = min(end, length)
        array = self.interpreter.ArrayConstructor.construct([])
        for new_index, old_index in enumerate(range(start, end)):
            p = unicode(old_index)
            if o.has_property(p):
                value = o.get(p)
                desc = PropertyDescriptor(
                    value=value, writable=True, enumerable=True, configurable=True
                )
                array.define_own_property(unicode(new_index), desc, False)
        return array

    def sort_compare(self, obj, j, k, comparefn):
        """
        Default sort comparison callback.
        """
        to_string = self.interpreter.to_string
        to_int32 = self.interpreter.to_int32
        j = to_string(j)
        k = to_string(k)
        hasj = obj.has_property(j)
        hask = obj.has_property(k)
        if hasj is False and hask is False:
            return 0
        elif hasj is False:
            return 1
        elif hask is False:
            return -1
        x = obj.get(j)
        y = obj.get(k)
        if x is Undefined and y is Undefined:
            return 0
        elif x is Undefined:
            return 1
        elif y is Undefined:
            return -1
        if comparefn is not Undefined:
            # Here we need to make sure that cmp will return an integer
            result = comparefn.call(Undefined, [x, y])
            return to_int32(result)
        return cmp(to_string(x), to_string(y))

    def sort_method(self, this, arguments):
        """
        ``Array.prototype.sort`` implementation.

        15.4.4.11
        """
        o = self.interpreter.to_object(this)
        length = self.interpreter.to_uint32(o.get('length'))
        comparefn = get_arguments(arguments, count=1)
        if comparefn is not Undefined and not is_callable(comparefn):
            raise ESTypeError('comparefn is not a function')
        # Let Python do the sorting
        indexes = range(length)
        array = [o.get(unicode(i)) for i in range(length)]
        indexes.sort(cmp=lambda j,k: self.sort_compare(o, j, k, comparefn))
        for i, index in enumerate(indexes):
            o.put(unicode(i), array[index], False)
        return o

    def splice_method(self, this, arguments):
        """
        ``Array.prototype.splice`` implementation.

        15.4.4.12
        """
        o = self.interpreter.to_object(this)
        length = self.interpreter.to_uint32(o.get('length'))
        start, delete_count = get_arguments(arguments, count=2)
        start = self.interpreter.to_integer(start)
        if start < 0:
            start = max(length + start, 0)
        else:
            start = min(start, length)
        delete_count = self.interpreter.to_integer(delete_count)
        delete_count = min(max(delete_count, 0), length - start)
        array = self.interpreter.ArrayConstructor.construct([])
        for k in range(delete_count):
            from_index = unicode(k + start)
            if o.has_property(from_index):
                from_value = o.get(from_index)
                desc = PropertyDescriptor(
                    value=from_value, writable=True, enumerable=True, configurable=True
                )
                array.define_own_property(unicode(k), desc, False)
            k = k + 1
        items = arguments[2:]
        num_items = len(items)
        if num_items < delete_count:
            k = start
            while k < (num_items - delete_count):
                from_index = unicode(k + delete_count)
                to_index = unicode(k + num_items)
                if o.has_property(from_index):
                    from_value = o.get(from_index)
                    o.put(to_index, from_value, True)
                else:
                    o.delete(to_index, True)
                k = k + 1
            k = length
            while k > (length - num_items + delete_count):
                o.delete(unicode(k - 1), True)
                k = k - 1
        else:
            k = length - delete_count
            while k > start:
                from_index = unicode(k + delete_count - 1)
                to_index = unicode(k + num_items - 1)
                if o.has_property(from_index):
                    from_value = o.get(from_index)
                    o.put(to_index, from_value, True)
                else:
                    o.delete(to_index, True)
                k = k - 1
        for k, item in enumerate(items, length):
            o.put(unicode(k), item, True)
        o.put('length', (length - delete_count + num_items), True)
        return array

    def unshift_method(self, this, arguments):
        """
        ``Array.prototype.unshift`` implementation.

        15.4.4.13
        """
        o = self.interpreter.to_object(this)
        length = self.interpreter.to_uint32(o.get('length'))
        arg_count = len(arguments)
        for k in range(length, 0, -1):
            from_index = unicode(k - 1)
            to_index = unicode(k + arg_count - 1)
            if o.has_property(from_index):
                val = o.get(from_index)
                o.put(to_index, val, True)
            else:
                o.delete(to_index, True)
        for i, item in enumerate(arguments):
            o.put(unicode(i), item, True)
        o.put('length', length + arg_count, True)
        return length + arg_count

    def index_of_method(self, this, arguments):
        """
        ``Array.prototype.indexOf`` implementation.

        15.4.4.14
        """
        o = self.interpreter.to_object(this)
        length = self.interpreter.to_uint32(o.get('length'))
        if length == 0:
            return -1
        search_element, from_index = get_arguments(arguments, count=2)
        from_index = self.interpreter.to_integer(from_index)
        if from_index < 0:
            from_index = max(0, length - abs(from_index))
        index = from_index
        strict_equal = self.interpreter.strict_equal
        while index < length:
            key = unicode(index)
            if o.has_property(key):
                element = o.get(key)
                if strict_equal(element, search_element):
                    return index
            index = index + 1
        return -1

    def last_index_of_method(self, this, arguments):
        """
        ``Array.prototype.lastIndexOf`` implementation.

        15.4.4.15
        """
        o = self.interpreter.to_object(this)
        length = self.interpreter.to_uint32(o.get('length'))
        if length == 0:
            return -1
        search_element, from_index = get_arguments(arguments, count=2)
        from_index = self.interpreter.to_integer(from_index)
        if from_index >= 0:
            from_index = min(from_index, length - 1)
        else:
            from_index = length - abs(from_index)
        index = from_index
        while index >= 0:
            key = unicode(index)
            if o.has_property(key):
                element = o.get(key)
                if self.interpreter.strict_equal(element, search_element):
                    return index
            index = index - 1
        return -1

    def every_method(self, this, arguments):
        """
        ``Array.prototype.every`` implementation.

        15.4.4.16
        """
        o = self.interpreter.to_object(this)
        length = self.interpreter.to_uint32(o.get('length'))
        callback, this_arg = get_arguments(arguments, count=2)
        if not is_callable(callback):
            raise ESTypeError('callback is not a function')
        to_boolean = self.interpreter.to_boolean
        for i in range(length):
            index = unicode(i)
            if o.has_property(index):
                value = o.get(index)
                result = callback.call(this_arg, [value, i, o])
                if to_boolean(result) is False:
                    return False
        return True

    def some_method(self, this, arguments):
        """
        ``Array.prototype.some`` implementation.

        15.4.4.17
        """
        o = self.interpreter.to_object(this)
        length = self.interpreter.to_uint32(o.get('length'))
        callback, this_arg = get_arguments(arguments, count=2)
        if not is_callable(callback):
            raise ESTypeError('callback is not a function')
        to_boolean = self.interpreter.to_boolean
        for i in range(length):
            index = unicode(i)
            if o.has_property(index):
                value = o.get(index)
                result = callback.call(this_arg, [value, i, o])
                if to_boolean(result) is True:
                    return True
        return False

    def for_each_method(self, this, arguments):
        """
        ``Array.prototype.forEach`` implementation.

        15.4.4.18
        """
        o = self.interpreter.to_object(this)
        length = self.interpreter.to_uint32(o.get('length'))
        callback, this_arg = get_arguments(arguments, count=2)
        if not is_callable(callback):
            raise ESTypeError('callback is not a function')
        for i in range(length):
            index = unicode(i)
            if o.has_property(index):
                value = o.get(index)
                result = callback.call(this_arg, [value, i, o])
        return Undefined

    def map_method(self, this, arguments):
        """
        ``Array.prototype.map`` implementation.

        15.4.4.19
        """
        o = self.interpreter.to_object(this)
        length = self.interpreter.to_uint32(o.get('length'))
        callback, this_arg = get_arguments(arguments, count=2)
        if not is_callable(callback):
            raise ESTypeError('callback is not a function')
        array = self.interpreter.ArrayConstructor.construct([length])
        for i in range(length):
            index = unicode(i)
            if o.has_property(index):
                value = o.get(index)
                result = callback.call(this_arg, [value, i, o])
                desc = PropertyDescriptor(
                    value=result, writable=True, enumerable=True, configurable=True
                )
                array.define_own_property(index, desc, False)
        return array

    def filter_method(self, this, arguments):
        """
        ``Array.prototype.filter`` implementation.

        15.4.4.20
        """
        o = self.interpreter.to_object(this)
        length = self.interpreter.to_uint32(o.get('length'))
        callback, this_arg = get_arguments(arguments, count=2)
        if not is_callable(callback):
            raise ESTypeError('callback is not a function')
        array = self.interpreter.ArrayConstructor.construct([])
        to_boolean = self.interpreter.to_boolean
        target_index = 0
        for i in range(length):
            index = unicode(i)
            if o.has_property(index):
                value = o.get(index)
                result = callback.call(this_arg, [value, i, o])
                if to_boolean(result) is True:
                    desc = PropertyDescriptor(
                        value=value, writable=True, enumerable=True, configurable=True
                    )
                    array.define_own_property(unicode(target_index), desc, False)
                    target_index = target_index + 1
        return array

    def reduce_method(self, this, arguments):
        """
        ``Array.prototype.reduce`` implementation.

        15.4.4.21
        """
        o = self.interpreter.to_object(this)
        length = self.interpreter.to_uint32(o.get('length'))
        callback, initial_value = get_arguments(arguments, count=2)
        if not is_callable(callback):
            raise ESTypeError('callback is not a function')
        accumulator = None
        if len(arguments) < 2:
            if length == 0:
                raise ESTypeError()
            for i in range(length):
                index = unicode(i)
                if o.has_property(index):
                    accumulator = o.get(index)
                    break
            if accumulator is None:
                raise ESTypeError()
        else:
            accumulator = initial_value
        for i in range(length):
            index = unicode(i)
            if o.has_property(index):
                value = o.get(index)
                accumulator = callback.call(this, [accumulator, value, i, o])
        return accumulator

    def reduce_right_method(self, this, arguments):
        """
        ``Array.prototype.reduceRight`` implementation.

        15.4.4.22
        """
        o = self.interpreter.to_object(this)
        length = self.interpreter.to_uint32(o.get('length'))
        callback, initial_value = get_arguments(arguments, count=2)
        if not is_callable(callback):
            raise ESTypeError('callback is not a function')
        accumulator = None
        if len(arguments) < 2:
            if length == 0:
                raise ESTypeError()
            for i in range(length - 1, -1, -1):
                index = unicode(i)
                if o.has_property(index):
                    accumulator = o.get(index)
                    break
            if accumulator is None:
                raise ESTypeError()
        else:
            accumulator = initial_value
        for i in range(length - 1, -1, -1):
            index = unicode(i)
            if o.has_property(index):
                value = o.get(index)
                accumulator = callback.call(this, [accumulator, value, i, o])
        return accumulator
