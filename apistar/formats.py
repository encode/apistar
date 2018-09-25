import datetime
import re

from apistar.exceptions import ErrorMessage, ValidationError

DATE_REGEX = re.compile(
    r'(?P<year>\d{4})-(?P<month>\d{1,2})-(?P<day>\d{1,2})$'
)

TIME_REGEX = re.compile(
    r'(?P<hour>\d{1,2}):(?P<minute>\d{1,2})'
    r'(?::(?P<second>\d{1,2})(?:\.(?P<microsecond>\d{1,6})\d{0,6})?)?'
)

DATETIME_REGEX = re.compile(
    r'(?P<year>\d{4})-(?P<month>\d{1,2})-(?P<day>\d{1,2})'
    r'[T ](?P<hour>\d{1,2}):(?P<minute>\d{1,2})'
    r'(?::(?P<second>\d{1,2})(?:\.(?P<microsecond>\d{1,6})\d{0,6})?)?'
    r'(?P<tzinfo>Z|[+-]\d{2}(?::?\d{2})?)?$'
)


class BaseFormat:
    def error(self, code, **context):
        message = self.error_message(code, **context)
        raise ValidationError(messages=[message])

    def error_message(self, code, **context):
        text = self.errors[code].format(**self.__dict__, **context)
        return ErrorMessage(text=text, code=code)

    def is_native_type(self, value):
        raise NotImplementedError()

    def validate(self, value):
        raise NotImplementedError()

    def to_string(self, value):
        raise NotImplementedError()


class DateFormat(BaseFormat):
    errors = {
        'format': 'Must be a valid date.'
    }

    def is_native_type(self, value):
        return isinstance(value, datetime.date)

    def validate(self, value):
        match = DATE_REGEX.match(value)
        if not match:
            self.error('format')

        kwargs = {k: int(v) for k, v in match.groupdict().items()}
        return datetime.date(**kwargs)

    def to_string(self, value):
        return value.isoformat()


class TimeFormat(BaseFormat):
    errors = {
        'format': 'Must be a valid time.'
    }

    def is_native_type(self, value):
        return isinstance(value, datetime.time)

    def validate(self, value):
        match = TIME_REGEX.match(value)
        if not match:
            self.error('format')

        kwargs = match.groupdict()
        kwargs['microsecond'] = kwargs['microsecond'] and kwargs['microsecond'].ljust(6, '0')
        kwargs = {k: int(v) for k, v in kwargs.items() if v is not None}
        return datetime.time(**kwargs)

    def to_string(self, value):
        return value.isoformat()


class DateTimeFormat(BaseFormat):
    errors = {
        'format': 'Must be a valid datetime.'
    }

    def is_native_type(self, value):
        return isinstance(value, datetime.datetime)

    def validate(self, value):
        match = DATETIME_REGEX.match(value)
        if not match:
            self.error('format')

        kwargs = match.groupdict()
        kwargs['microsecond'] = kwargs['microsecond'] and kwargs['microsecond'].ljust(6, '0')
        tzinfo = kwargs.pop('tzinfo')
        if tzinfo == 'Z':
            tzinfo = datetime.timezone.utc
        elif tzinfo is not None:
            offset_mins = int(tzinfo[-2:]) if len(tzinfo) > 3 else 0
            offset_hours = int(tzinfo[1:3])
            delta = datetime.timedelta(hours=offset_hours, minutes=offset_mins)
            if tzinfo[0] == '-':
                delta = -delta
            tzinfo = datetime.timezone(delta)
        kwargs = {k: int(v) for k, v in kwargs.items() if v is not None}
        kwargs['tzinfo'] = tzinfo
        return datetime.datetime(**kwargs)

    def to_string(self, value):
        value = value.isoformat()
        if value.endswith('+00:00'):
            value = value[:-6] + 'Z'
        return value
