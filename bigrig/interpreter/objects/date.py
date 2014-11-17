"""
Specification objects and functions for the ``Date`` built-in.
"""
from __future__ import absolute_import
import time
import math
import operator
from .base import ObjectInstance, FunctionInstance
from .function import define_native_method
from ..literals import LiteralParser, LiteralParseError
from ..types import (
    NaN, inf, Undefined, Null, StringType, ObjectType, get_arguments,
    get_primitive_type
)

# primitive_value is a number, representing ms since unix epoch
DIGITS = set('0123456789')
MS_PER_DAY = 86400000
AVERAGE_DAYS_PER_YEAR = 365.2425
HOURS_PER_DAY = 24
MINUTES_PER_HOUR = 60
SECONDS_PER_MINUTE = 60
MS_PER_SECOND = 1000
MS_PER_MINUTE = 60000
MS_PER_HOUR = 3600000

WEEKDAY_NAMES = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat']
MONTH_NAMES = [
    'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'July', 'Aug', 'Sep',
    'Oct', 'Nov', 'Dec'
]
MONTH_START_DAYS = [
    0, 31, 59, 90, 120, 151, 181, 212, 243, 273, 304, 334
]
MONTH_START_DAYS_LEAP_YEAR = [
    0, 31, 60, 91, 121, 152, 182, 213, 244, 274, 305, 335
]

#
# Internal specification helper functions
#

def finite(x):
    """
    Is the given value a non-infinite number?
    """
    return not (math.isnan(x) or x == inf or x == -inf)


def day(t):
    """
    Number of days represented by the given milliseconds.

    15.9.1.2
    """
    return t // MS_PER_DAY


def time_within_day(t):
    """
    The remainder when converting ms to number of days.
   
    15.9.1.2
    """
    return t % MS_PER_DAY


def day_from_year(y):
    """
    The day number of the first day of the given year.

    15.9.1.3
    """
    return 365 * (y - 1970) + ((y - 1969) // 4) - ((y - 1901) // 100) + ((y - 1601) // 400)


def days_in_year(y):
    """
    The number of days in the given year.

    15.9.1.3
    """
    if (y % 4) != 0:
        return 365
    if (y % 4) == 0 and (y % 100) != 0:
        return 366
    if (y % 100) == 0 and (y % 400) != 0:
        return 365
    if (y % 400) == 0:
        return 366
    return 365


def time_from_year(y):
    """
    The time value at the start of the given year.

    15.9.1.3
    """
    return MS_PER_DAY * day_from_year(y)


def year_from_time(t):
    """
    The year that the given time falls within.

    15.9.1.3
    """
    y = int(((float(t) / float(MS_PER_DAY)) / AVERAGE_DAYS_PER_YEAR) + 1970)
    t2 = time_from_year(y)
    if t2 > t:
        y = y - 1
    elif (t2 + MS_PER_DAY * days_in_year(y)) <= t:
        y = y + 1
    return y


def in_leap_year(t):
    """
    Is the year that the given time falls within a leap year?

    15.9.1.3
    """
    y = year_from_time(t)
    return int(days_in_year(y) == 366)


def day_within_year(t):
    """
    The number of the day the given time is in relative to the start of the
    year the time falls within.

    15.9.1.4
    """
    return day(t) - day_from_year(year_from_time(t))


def month_from_time(t):
    """
    The 0-based number of the month in the year the given time falls within.
    
    15.9.1.4
    """
    leap_year = in_leap_year(t)
    day_in_year = day_within_year(t)
    month_start_days = in_leap_year(t) and MONTH_START_DAYS_LEAP_YEAR or MONTH_START_DAYS
    for i, start_day in enumerate(month_start_days[1:]):
        if day_in_year < start_day:
            return i
    return 11


def date_from_time(t):
    """
    The 1-based number of date within the month the given time falls within.

    15.9.1.5
    """
    day_in_year = day_within_year(t) + 1 # Adjust to 1-based
    month = month_from_time(t)
    month_start_days = in_leap_year(t) and MONTH_START_DAYS_LEAP_YEAR or MONTH_START_DAYS
    month_start_day = month_start_days[month]
    return day_in_year - month_start_day


def days_in_month(month, in_leap):
    """
    Given the 0-based index of the month, return the number of days in the
    month in the given in_leap context.
    """
    month = month % 12
    if month in (3, 5, 8, 10):
        return 30
    elif month in (0, 2, 4, 6, 7, 9, 11):
        return 31
    elif in_leap and month == 1:
        return 29
    elif month == 1:
        return 28


def week_day(t):
    """
    Return the 0-based index of the weekday the time falls within.

    15.9.1.6
    """
    return (day(t) + 4) % 7


def hour_from_time(t):
    """
    The 0-based hour in the day the given time falls within.

    15.9.1.10
    """
    return (t // MS_PER_HOUR) % HOURS_PER_DAY


def min_from_time(t):
    """
    The 0-based minute in the hour the given time falls within.

    15.9.1.10
    """
    return (t // MS_PER_MINUTE) % MINUTES_PER_HOUR


def sec_from_time(t):
    """
    The 0-based second in the minute the given time falls within.

    15.9.1.10
    """
    return (t // MS_PER_SECOND) % SECONDS_PER_MINUTE


def ms_from_time(t):
    """
    The 0-based millisecond in the minute the given time falls within.

    15.9.1.10
    """
    return t % MS_PER_SECOND


def local_tza():
    """
    Return the local standard timezone adjustment in milliseconds.

    15.9.1.7
    """
    return -(time.timezone * MS_PER_SECOND)


def make_date(day, time):
    """
    Return the ms representation of the given date number and ms within that
    given date.

    15.9.1.13
    """
    if not finite(day) or not finite(time):
        return NaN
    return day * MS_PER_DAY + time


def make_time(hour, minute, sec, ms, to_integer=None):
    """
    Calculate the milliseconds represented by the given time parts.

    15.9.1.11
    """
    if not finite(hour) or not finite(minute) or not finite(sec) or not finite(ms):
        return NaN
    if to_integer is None:
        to_integer = lambda x: int(x)
    return to_integer(hour) * MS_PER_HOUR + to_integer(minute) * MS_PER_MINUTE + to_integer(sec) * MS_PER_SECOND + to_integer(ms)


def make_day(year, month, date, to_integer=None):
    """
    Calculate the day number represented by the given date parts.

    Note that the ``to_integer`` parameter may be given to provide the
    appropriate conversion for an ES execution context.

    15.9.1.12
    """
    if not finite(year) or not finite(month) or not finite(date):
        return NaN
    if to_integer is None:
        to_integer = int
    year = to_integer(year)
    month = to_integer(month)
    date = to_integer(date)
    ym = year + (month // 12)
    mn = month % 12
    sign = year < 1970 and -1 or 1
    t = year < 1970 and 1 or 0
    y = year < 1970 and 1969 or 1970
    compare = (sign == -1) and operator.ge or operator.lt
    while compare(y, year):
        t = t + (sign * days_in_year(y) * MS_PER_DAY)
        y = y + sign
    for i in range(mn):
        leap = in_leap_year(t)
        t = t + days_in_month(i, leap) * MS_PER_DAY
    if not year_from_time(t) == ym:
        return NaN
    if not month_from_time(t) == mn:
        return NaN
    if not date_from_time(t) == 1:
        return NaN
    return day(t) + date - 1


def time_clip(time, to_integer=None):
    """
    Convert the ECMAScript number value to a number of milliseconds.

    15.9.1.14
    """
    if to_integer is None:
        to_integer = int
    if not finite(time):
        return NaN
    if abs(time) > 8.64e15:
        return NaN
    return to_integer(time)


def next_sunday(t):
    """
    Compute the next calendar Sunday from the given time.
    """
    day = week_day(t)
    if day != 0:
        t = t + (7 - day) * MS_PER_DAY
    return t


def in_dst(t, to_integer=None):
    """
    Determine whether the given time is in an alternate timezone.
    """
    if to_integer is not None:
        time = lambda h, m, s, ms: make_time(h, m, s, ms, to_integer=to_integer)
        day = lambda y, m, d: make_day(y, m, d, to_integer=to_integer)
    else:
        time = make_time
        day = make_day
    year = year_from_time(t)
    time = make_time(2, 0, 0, 0)
    if year <= 2006:
        start = next_sunday(make_date(make_day(year, 3, 1), time))
        end = next_sunday(make_date(make_day(year, 9, 24), time))
    else:
        start = next_sunday(make_date(make_day(year, 2, 7), time))
        end = next_sunday(make_date(make_day(year, 10, 1), time))
    return start <= t < end


def daylight_saving_ta(t):
    """
    The offset for the effective daylight saving time the time falls within.

    15.9.1.8
    """
    # time_in_year = t - time_from_year(year_from_time(t))
    # leap_year = in_leap_year(t)
    # year_start_week_day = week_day(time_from_year(year_from_time(t)))
    ta = 0
    # if in_dst(t):
    #    ta = -((time.altzone - time.timezone) * 1000)
    return ta


def local_time(t):
    """
    Compute the local time from the given UTC time.

    15.9.1.9
    """
    return t + local_tza() + daylight_saving_ta(t)


def utc(t):
    """
    Compute the UTC time from the given local time.
    """
    return t - local_tza() + daylight_saving_ta(t - local_tza())


#
# Parser objects for the ECMAScript date time string format
#

class DateParseError(Exception):
    """
    Invalid ECMAScript date time formatted string.
    """
    pass


class DateTimeParser(LiteralParser):
    """
    Parse ECMAScript date time formatted strings.

    15.9.1.15
    """
    def expect_digit(self):
        if self.peek() not in DIGITS:
            raise LiteralParseError()
        return self.advance()

    def consume_int(self, digits):
        return int(u''.join([self.expect_digit() for i in range(digits)]))

    def parse_date(self):
        """
        YYYY[-MM[-DD]]
        """
        year = self.consume_int(4)
        month = 1
        day = 1
        if self.peek() == '-':
            self.expect('-')
            month = self.consume_int(2)
        else:
            return (year, month, day)
        if self.peek() == '-':
            self.expect('-')
            day = self.consume_int(2)
        return (year, month, day)

    def parse_time(self):
        """
        THH:mm[:ss[.sss]]
        """
        self.expect('T')
        hour = self.consume_int(2)
        self.expect(':')
        minutes = self.consume_int(2)
        seconds = 0
        ms = 0
        if self.peek(':'):
            self.expect(':')
            seconds = self.consume_int(2)
        else:
            return
        if self.peek('.'):
            self.expect('.')
            ms = self.consume_int(3)
        return (hour, minutes, seconds)

    def parse_offset(self):
        """
        Z | (+|-)HH:mm
        """
        sign = 1
        hours = 0
        minutes = 0
        next_char = self.peek()
        if next_char == 'Z':
            self.expect('Z')
            self.expect('')
            return 0
        elif next_char == '-':
            self.expect('-')
            sign = -1
        elif next_char == '+':
            self.expect('+')
            sign = 1
        else:
            raise LiteralParseError()
        hours = self.consume_int(2)
        self.expect(':')
        minutes = self.consume_int(2)
        offset = (hours * MS_IN_HOUR) + (minutes * MS_IN_MINUTES)
        return sign * offset

    def parse(self):
        """
        Return the time represented by the ECMAScript date time formatted
        string.
        """
        try:
            year, month, day = self.parse_date()
            result = make_date(make_day(year, month-1, day-1), 0)
            next_char = self.peek()
            if next_char == 'T':
                hour, minutes, seconds, ms = self.parse_time()
                result = result + make_time(hour, minutes, seconds, ms)
            elif next_char != '':
                return NaN
            next_char = self.peek()
            if next_char == 'Z' or next_char == '+' or next_char == '-':
                offset = self.parse_offset()
                result = result + offset
            next_char = self.peek()
            if next_char != '':
                return NaN
            return result
        except LiteralParseError:
            return NaN


def parse_datetime(string):
    parser = DateTimeParser(string)
    return parser.parse()

#
# Specification objects
#

class DateInstance(ObjectInstance):
    """
    The specialized ``Date`` class object.

    15.9.6
    """
    es_class = "Date"
    def __init__(self, interpreter, primitive_value):
        super(DateInstance, self).__init__(interpreter)
        self.primitive_value = primitive_value

    def default_value(self, hint='String'):
        """
        8.12.8
        """
        if hint is None:
            hint = 'String'
        return super(DateInstance, self).default_value(hint=hint)


class DateConstructor(FunctionInstance):
    """
    The  ``Date`` constructor function.

    15.9.2 & 15.9.3
    """
    def __init__(self, interpreter):
        super(DateConstructor, self).__init__(interpreter)
        self.prototype = interpreter.FunctionPrototype
        define_native_method(self, 'parse', self.parse_method, 1)
        define_native_method(self, 'UTC', self.utc_method, 7)
        define_native_method(self, 'now', self.now_method)

    def time_clip(self, t):
        """
        """
        return time_clip(t, to_integer=self.interpreter.to_integer)

    def make_date_instance(self, primitive_value):
        """
        """
        obj = DateInstance(self.interpreter, primitive_value)
        obj.prototype = self.interpreter.DatePrototype
        obj.set_property('prototype', self.interpreter.DatePrototype)
        return obj

    #
    # Internal Specification Methods
    #

    def call(self, this, arguments):
        """
        15.9.2
        """
        obj = self.construct(arguments)
        return self.interpreter.to_string(obj)

    def construct(self, arguments):
        """
        15.9.3.1
        """
        to_number = self.interpreter.to_number
        num_args = len(arguments)
        v = None
        if num_args == 0:
            return self.now_method(None, [])
        elif num_args == 1:
            v = self.interpreter.to_primitive(arguments[0])
            if get_primitive_type(v) is StringType:
                v = self.parse_method(None, [v])
            else:
                v = to_number(v)
            primitive_value = self.time_clip(v)
        else:
            def get_arguments(arguments, defaults):
                values = []
                num_arguments = len(arguments)
                for i in range(7):
                    if i < num_arguments:
                        v = to_number(arguments[0])
                    else:
                        v = defaults[i]
                    values.append(v)
                return values
            year, month, date, hours, minutes, seconds, ms = get_arguments(
                arguments, [Undefined, Undefined, 1, 0, 0, 0, 0]
            )
            if not math.isnan(year) and 0 <= year <= 99:
                year = 1900 + year
            final_date = make_date(
                make_day(year, month, date),
                make_time(hours, minutes, seconds, ms)
            )
            primitive_value = self.time_clip(utc(final_date))
        return self.make_date_instance(primitive_value)

    #
    # Method property implementations
    #

    def parse_method(self, this, arguments):
        """
        ``Date.parse`` method implementation.

        15.9.4.2
        """
        string = Undefined
        if arguments:
            string = arguments[0]
        string = self.interpreter.to_string(string)
        primitive_value = parse_datetime(string)
        return self.make_date_instance(primitive_value)

    def utc_method(self, this, arguments):
        """
        ``Date.UTC`` method implementation.

        15.9.4.3
        """
        def get_arguments(arguments, defaults):
            values = []
            num_arguments = len(arguments)
            for i in range(7):
                if i < num_arguments:
                    v = to_number(arguments[0])
                else:
                    v = defaults[i]
                values.append(v)
            return values
        year, month, date, hours, minutes, seconds, ms = get_arguments(
            arguments, [Undefined, Undefined, 1, 0, 0, 0, 0]
        )
        if not math.isnan(year) and 0 <= y <= 99:
            year = 1900 + year
        final_date = make_date(
            make_day(year, month, date),
            make_time(hours, minutes, seconds, ms)
        )
        primitive_value = self.time_clip(final_date)
        return self.make_date_instance(primitive_value)

    def now_method(self, this, arguments):
        """
        ``Date.now`` method implementation.

        15.9.4.4
        """
        primitive_value = self.time_clip(int(time.time() * 1000))
        return self.make_date_instance(primitive_value)
        


class DatePrototype(DateInstance):
    """
    The prototype object assigned to ``Date`` instances.

    15.9.5
    """
    def __init__(self, interpreter):
        super(DatePrototype, self).__init__(interpreter, NaN)
        self.prototype = interpreter.ObjectPrototype
        define_native_method(self, 'toString', self.to_string_method)
        define_native_method(self, 'toDateString', self.to_date_string_method)
        define_native_method(self, 'toTimeString', self.to_time_string_method)
        define_native_method(self, 'toLocaleString', self.to_locale_string_method)
        define_native_method(self, 'toLocaleDateString', self.to_locale_date_string_method)
        define_native_method(self, 'toLocaleTimeString', self.to_locale_time_string_method)
        define_native_method(self, 'valueOf', self.value_of_method)
        define_native_method(self, 'getTime', self.get_time_method)
        define_native_method(self, 'getFullYear', self.get_full_year_method)
        define_native_method(self, 'getUTCFullYear', self.get_utc_full_year_method)
        define_native_method(self, 'getMonth', self.get_month_method)
        define_native_method(self, 'getUTCMonth', self.get_utc_month_method)
        define_native_method(self, 'getDate', self.get_date_method)
        define_native_method(self, 'getUTCDate', self.get_utc_date_method)
        define_native_method(self, 'getDay', self.get_day_method)
        define_native_method(self, 'getUTCDay', self.get_utc_day_method)
        define_native_method(self, 'getHours', self.get_hours_method)
        define_native_method(self, 'getUTCHours', self.get_utc_hours_method)
        define_native_method(self, 'getMinutes', self.get_minutes_method)
        define_native_method(self, 'getUTCMinutes', self.get_utc_minutes_method)
        define_native_method(self, 'getSeconds', self.get_seconds_method)
        define_native_method(self, 'getUTCSeconds', self.get_utc_seconds_method)
        define_native_method(self, 'getMilliseconds', self.get_milliseconds_method)
        define_native_method(self, 'getUTCMilliseconds', self.get_utc_milliseconds_method)
        define_native_method(self, 'getTimezoneOffset', self.get_timezone_offset_method)
        define_native_method(self, 'setTime', self.set_time_method, 1)
        define_native_method(self, 'setMilliseconds', self.set_milliseconds_method, 1)
        define_native_method(self, 'setUTCMilliseconds', self.set_utc_milliseconds_method, 1)
        define_native_method(self, 'setSeconds', self.set_seconds_method, 2)
        define_native_method(self, 'setUTCSeconds', self.set_utc_seconds_method, 2)
        define_native_method(self, 'setMinutes', self.set_minutes_method, 3)
        define_native_method(self, 'setUTCMinutes', self.set_utc_minutes_method, 3)
        define_native_method(self, 'setHours', self.set_hours_method, 4)
        define_native_method(self, 'setUTCHours', self.set_utc_hours_method, 4)
        define_native_method(self, 'setDate', self.set_date_method, 1)
        define_native_method(self, 'setUTCDate', self.set_utc_date_method, 1)
        define_native_method(self, 'setMonth', self.set_month_method, 2)
        define_native_method(self, 'setUTCMonth', self.set_utc_month_method, 2)
        define_native_method(self, 'setFullYear', self.set_full_year_method, 3)
        define_native_method(self, 'setUTCFullYear', self.set_utc_full_year_method, 3)
        define_native_method(self, 'toUTCString', self.to_utc_string_method)
        define_native_method(self, 'toISOString', self.to_iso_string_method)
        define_native_method(self, 'toJSON', self.to_json_method, 1)

    #
    # Internal helper methods
    #

    def time_clip(self, time):
        """
        """
        return time_clip(time, to_integer=self.interpreter.to_integer)

    def get_value(self, obj):
        """
        """
        if get_primitive_type(obj) is not ObjectType or obj.es_class != 'Date':
            string = self.interpreter.to_string(obj)
            raise ESTypeError('%s is not a Date object' % string)
        return obj.primitive_value

    def make_time_replace(self, t, arguments, possible_count):
        """
        """
        to_number = self.interpreter.to_number
        num_given = len(arguments)
        defaults = [hour_from_time, min_from_time, sec_from_time, ms_from_time]
        to_use = min(num_given, possible_count)
        args = [default(t) for default in defaults[:-possible_count]]
        args.extend(to_number(arg) for arg in arguments[:to_use])
        args.extend(default(t) for default in defaults[len(defaults)-possible_count+to_use:])
        return make_time(*args, to_integer=self.interpreter.to_integer)

    def set_time_component(self, this, arguments, possible_count, local=True):
        """
        """
        value = Undefined
        if arguments:
            value = arguments[0]
        value = self.interpreter.to_number(value)
        t = self.get_value(this)
        if local:
            t = local_time(t)
        time = self.make_time_replace(t, arguments, possible_count)
        d = make_date(day(t), time)
        if local:
            d = utc(d)
        u = self.time_clip(d)
        this.primitive_value = u
        return u

    def make_day_replace(self, t, arguments, possible_count):
        """
        """
        to_number = self.interpreter.to_number
        num_given = len(arguments)
        to_use = min(num_given, possible_count)
        defaults = [year_from_time, month_from_time, date_from_time]
        args = [default(t) for default in defaults[:-possible_count]]
        args.extend(to_number(arg) for arg in arguments[:to_use])
        args.extend(default(t) for default in defaults[len(defaults)-possible_count+to_use:])
        return make_day(*args, to_integer=self.interpreter.to_integer)

    def set_date_component(self, this, arguments, possible_count, local=True):
        """
        """
        primitive_value = self.get_value(this)
        if math.isnan(primitive_value):
            t = 0
        else:
            t = primitive_value
        if local:
            t = local_time(t)
        d = make_date(
            self.make_day_replace(t, arguments, possible_count),
            time_within_day(t)
        )
        if local:
            d = utc(d)
        u = self.time_clip(d)
        this.primitive_value = u
        return u

    #
    # Method property implementations
    #

    def to_string_method(self, this, arguments):
        """
        ``Date.prototype.toString`` method implementation.

        15.9.5.2
        """
        t = local_time(self.get_value(this))
        if math.isnan(t):
            return u'Invalid Date'
        year, month, day = year_from_time(t), month_from_time(t), date_from_time(t)
        hour, minutes, seconds = hour_from_time(t), min_from_time(t), sec_from_time(t)
        day_of_week = week_day(t)
        return u'%s %s %02d %d %02d:%02d:%02d' % (WEEKDAY_NAMES[day_of_week], MONTH_NAMES[month], day, year, hour, minutes, seconds)

    def to_date_string_method(self, this, arguments):
        """
        ``Date.prototype.toDateString`` method implementation.

        15.9.5.3
        """
        t = local_time(self.get_value(this))
        if math.isnan(t):
            return u'Invalid Date'
        year, month, day = year_from_time(t), month_from_time(t), date_from_time(t)
        day_of_week = week_day(t)
        return u'%s %s %02d %d' % (WEEKDAY_NAMES[day_of_week], MONTH_NAMES[month], day, year)

    def to_time_string_method(self, this, arguments):
        """
        ``Date.prototype.toTimeString`` method implementation.

        15.9.5.4
        """
        t = local_time(self.get_value(this))
        if math.isnan(t):
            return u'Invalid Date'
        hour, minutes, seconds = hour_from_time(t), min_from_time(t), sec_from_time(t)
        return u'%02d:%02d:%02d' % (hour, minutes, seconds)

    def to_locale_string_method(self, this, arguments):
        """
        ``Date.prototype.toLocaleString`` method implementation.

        15.9.5.5
        """
        return self.to_string(this, arguments)

    def to_locale_date_string_method(self, this, arguments):
        """
        ``Date.prototype.toLocaleDateString`` method implementation.

        15.9.5.6
        """
        return self.to_date_string(this, arguments)

    def to_locale_time_string_method(self, this, arguments):
        """
        ``Date.prototype.toLocaleTimeString`` method implementation.

        15.9.5.7
        """
        return self.to_time_string(this, arguments)

    def value_of_method(self, this, arguments):
        """
        ``Date.prototype.valueOf`` method implementation.

        15.9.5.8
        """
        return self.get_value(this)

    def get_time_method(self, this, arguments):
        """
        ``Date.prototype.getTime`` method implementation.

        15.9.5.9
        """
        return self.get_value(this)

    def get_full_year_method(self, this, arguments):
        """
        ``Date.prototype.getFullYear`` method implementation.

        15.9.5.10
        """
        t = self.get_value(this)
        if math.isnan(t):
            return NaN
        return year_from_time(local_time(t))

    def get_utc_full_year_method(self, this, arguments):
        """
        ``Date.prototype.getUTCFullYear`` method implementation.

        15.9.5.11
        """
        t = self.get_value(this)
        if math.isnan(t):
            return NaN
        return year_from_time(t)

    def get_month_method(self, this, arguments):
        """
        ``Date.prototype.getMonth`` method implementation.

        15.9.5.12
        """
        t = self.get_value(this)
        if math.isnan(t):
            return NaN
        return month_from_time(local_time(t))

    def get_utc_month_method(self, this, arguments):
        """
        ``Date.prototype.getUTCMonth`` method implementation.

        15.9.5.13
        """
        t = self.get_value(this)
        if math.isnan(t):
            return NaN
        return month_from_time(t)

    def get_date_method(self, this, arguments):
        """
        ``Date.prototype.getDate`` method implementation.

        15.9.5.14
        """
        t = self.get_value(this)
        if math.isnan(t):
            return NaN
        return date_from_time(local_time(t))

    def get_utc_date_method(self, this, arguments):
        """
        ``Date.prototype.getUTCDate`` method implementation.

        15.9.5.15
        """
        t = self.get_value(this)
        if math.isnan(t):
            return NaN
        return date_from_time(t)

    def get_day_method(self, this, arguments):
        """
        ``Date.prototype.getDay`` method implementation.

        15.9.5.16
        """
        t = self.get_value(this)
        if math.isnan(t):
            return NaN
        return week_day(local_time(t))

    def get_utc_day_method(self, this, arguments):
        """
        ``Date.prototype.getUTCDay`` method implementation.

        15.9.5.17
        """
        t = self.get_value(this)
        if math.isnan(t):
            return NaN
        return week_day(t)

    def get_hours_method(self, this, arguments):
        """
        ``Date.prototype.getHours`` method implementation.

        15.9.5.18
        """
        t = self.get_value(this)
        if math.isnan(t):
            return NaN
        return hour_from_time(local_time(t))

    def get_utc_hours_method(self, this, arguments):
        """
        ``Date.prototype.getUTCHours`` method implementation.

        15.9.5.19
        """
        t = self.get_value(this)
        if math.isnan(t):
            return NaN
        return hour_from_time(t)

    def get_minutes_method(self, this, arguments):
        """
        ``Date.prototype.getMinutes`` method implementation.

        15.9.5.20
        """
        t = self.get_value(this)
        if math.isnan(t):
            return NaN
        return min_from_time(local_time(t))

    def get_utc_minutes_method(self, this, arguments):
        """
        ``Date.prototype.getUTCMinutes`` method implementation.

        15.9.5.21
        """
        t = self.get_value(this)
        if math.isnan(t):
            return NaN
        return min_from_time(t)

    def get_seconds_method(self, this, arguments):
        """
        ``Date.prototype.getSeconds`` method implementation.

        15.9.5.22
        """
        t = self.get_value(this)
        if math.isnan(t):
            return NaN
        return sec_from_time(local_time(t))

    def get_utc_seconds_method(self, this, arguments):
        """
        ``Date.prototype.getUTCSeconds`` method implementation.

        15.9.5.23
        """
        t = self.get_value(this)
        if math.isnan(t):
            return NaN
        return sec_from_time(t)

    def get_milliseconds_method(self, this, arguments):
        """
        ``Date.prototype.getMilliseconds`` method implementation.

        15.9.5.24
        """
        t = self.get_value(this)
        if math.isnan(t):
            return NaN
        return ms_from_time(local_time(t))

    def get_utc_milliseconds_method(self, this, arguments):
        """
        ``Date.prototype.getUTCMilliseconds`` method implementation.

        15.9.5.25
        """
        t = self.get_value(this)
        if math.isnan(t):
            return NaN
        return ms_from_time(t)

    def get_timezone_offset_method(self, this, arguments):
        """
        ``Date.prototype.getTimezoneOffset`` method implementation.

        15.9.5.26
        """
        t = self.get_value(this)
        if math.isnan(t):
            return NaN
        return (t - local_time(t)) / MS_PER_MINUTE

    def set_time_method(self, this, arguments):
        """
        ``Date.prototype.setTime`` method implementation.

        15.9.5.27
        """
        t = get_arguments(arguments, count=1)
        v = self.time_clip(self.interpreter.to_number(t))
        this.primitive_value = v
        return v

    def set_milliseconds_method(self, this, arguments):
        """
        ``Date.prototype.setMilliseconds`` method implementation.

        15.9.5.28
        """
        return self.set_time_component(this, arguments, 1)

    def set_utc_milliseconds_method(self, this, arguments):
        """
        ``Date.prototype.setUTCMilliseconds`` method implementation.

        15.9.5.29
        """
        return self.set_time_component(this, arguments, 1, local=False)

    def set_seconds_method(self, this, arguments):
        """
        ``Date.prototype.setSeconds`` method implementation.

        15.9.5.30
        """
        return self.set_time_component(this, arguments, 2)

    def set_utc_seconds_method(self, this, arguments):
        """
        ``Date.prototype.setUTCSeconds`` method implementation.

        15.9.5.31
        """
        return self.set_time_component(this, arguments, 2, local=False)

    def set_minutes_method(self, this, arguments):
        """
        ``Date.prototype.setMinutes`` method implementation.

        15.9.5.32
        """
        return self.set_time_component(this, arguments, 3)

    def set_utc_minutes_method(self, this, arguments):
        """
        ``Date.prototype.setUTCMinutes`` method implementation.

        15.9.5.33
        """
        return self.set_time_component(this, arguments, 3, local=False)

    def set_hours_method(self, this, arguments):
        """
        ``Date.prototype.setHours`` method implementation.

        15.9.5.34
        """
        return self.set_time_component(this, arguments, 4)

    def set_utc_hours_method(self, this, arguments):
        """
        ``Date.prototype.setUTCHours`` method implementation.

        15.9.5.35
        """
        return self.set_time_component(this, arguments, 4, local=False)

    def set_date_method(self, this, arguments):
        """
        ``Date.prototype.setDate`` method implementation.

        15.9.5.36
        """
        return self.set_date_component(this, arguments, 1)

    def set_utc_date_method(self, this, arguments):
        """
        ``Date.prototype.setUTCDate`` method implementation.

        15.9.5.37
        """
        return self.set_date_component(this, arguments, 1, local=False)

    def set_month_method(self, this, arguments):
        """
        ``Date.prototype.setMonth`` method implementation.

        15.9.5.38
        """
        return self.set_date_component(this, arguments, 2)

    def set_utc_month_method(self, this, arguments):
        """
        ``Date.prototype.`` method implementation.

        15.9.5.39
        """
        return self.set_date_component(this, arguments, 2, local=False)

    def set_full_year_method(self, this, arguments):
        """
        ``Date.prototype.setFullYear`` method implementation.

        15.9.5.40
        """
        return self.set_date_component(this, arguments, 3)

    def set_utc_full_year_method(self, this, arguments):
        """
        ``Date.prototype.setUTCFullYear`` method implementation.

        15.9.5.41
        """
        return self.set_date_component(this, arguments, 3, local=False)

    def to_utc_string_method(self, this, arguments):
        """
        ``Date.prototype.toUTCString`` method implementation.

        15.9.5.42
        """
        t = self.get_value(this)
        if math.isnan(t):
            return u'Invalid Date'
        year, month, day = year_from_time(t), month_from_time(t), date_from_time(t)
        hour, minutes, seconds = hour_from_time(t), min_from_time(t), sec_from_time(t)
        day_of_week = week_day(t)
        return u'%s %s %02d %d %02d:%02d:%02d' % (WEEKDAY_NAMES[day_of_week], MONTH_NAMES[month], day, year, hour, minutes, seconds)

    def to_iso_string_method(self, this, arguments):
        """
        ``Date.prototype.toISOString`` method implementation.

        15.9.5.43
        """
        t = self.get_value(this)
        if not finite(t):
            raise ESRangeError('Invalid time value')
        year, month, day = year_from_time(t), month_from_time(t), date_from_time(t)
        hour, minutes, seconds = hour_from_time(t), min_from_time(t), sec_from_time(t)
        return u'%04d-%02d-%02dT%02d:%02d:%02dZ'

    def to_json_method(self, this, arguments):
        """
        ``Date.prototype.toJSON`` method implementation.

        15.9.5.44
        """
        o = self.interpreter.to_object(this)
        tv = self.interpreter.to_primitive(o, 'Number')
        if get_primitive_type(tv) is NumberType and not finite(tv):
            return Null
        to_iso = o.get('toISOString')
        if is_callable(to_iso) is False:
            raise ESTypeError('toISOString is not a function')
        return to_iso.call(this, [])
