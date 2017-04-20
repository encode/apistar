import re
from typing import Any, Dict, List, Tuple, Union  # noqa

from apistar.exceptions import SchemaError, ValidationError


# TODO: Validation errors
# TODO: Error on unknown attributes
# TODO: allow_blank?
# TODO: format (check type at start and allow, coerce, .native)
# TODO: Enum
# TODO: Array
# TODO: default=empty
# TODO: check 'required' exists in 'properties'
# TODO: smarter ordering
# TODO: extra_properties=False by default
# TODO: inf, -inf, nan
# TODO: Overriding errors
# TODO: Blank booleans as False?


def validate(schema, value):
    try:
        return schema(value)
    except SchemaError as exc:
        raise ValidationError(message=str(exc))


class String(str):
    native_type = str
    errors = {
        'blank': 'Must not be blank.',
        'max_length': 'Must have no more than {max_length} characters.',
        'min_length': 'Must have at least {min_length} characters.',
        'pattern': 'Must match the pattern /{pattern}/.',
        'format': 'Must be a valid {format}.',
    }
    max_length = None  # type: int
    min_length = None  # type: int
    pattern = None  # type: str
    format = None  # type: Any
    trim_whitespace = True

    def __new__(cls, *args, **kwargs):
        assert len(args) == 1 and not kwargs
        value = str.__new__(cls, *args)

        if cls.trim_whitespace:
            value = value.strip()

        if cls.min_length is not None:
            if len(value) < cls.min_length:
                if cls.min_length == 1:
                    raise SchemaError(cls, 'blank')
                else:
                    raise SchemaError(cls, 'min_length')

        if cls.max_length is not None:
            if len(value) > cls.max_length:
                raise SchemaError(cls, 'max_length')

        if cls.pattern is not None:
            if not re.search(cls.pattern, value):
                raise SchemaError(cls, 'pattern')

        return value


class _NumericType(object):
    """
    Base class for both `Number` and `Integer`.
    """
    native_type = None  # type: type
    errors = {
        'type': 'Must be a valid number.',
        'minimum': 'Must be greater than or equal to {minimum}.',
        'exclusive_minimum': 'Must be greater than {minimum}.',
        'maximum': 'Must be less than or equal to {maximum}.',
        'exclusive_maximum': 'Must be less than {maximum}.',
        'multiple_of': 'Must be a multiple of {multiple_of}.',
    }
    minimum = None  # type: Union[float, int]
    maximum = None  # type: Union[float, int]
    exclusive_minimum = False
    exclusive_maximum = False
    multiple_of = None  # type: Union[float, int]

    def __new__(cls, *args, **kwargs):
        assert len(args) == 1 and not kwargs
        value = args[0]
        try:
            value = cls.native_type.__new__(cls, value)
        except (TypeError, ValueError):
            raise SchemaError(cls, 'type')

        if cls.minimum is not None:
            if cls.exclusive_minimum:
                if value <= cls.minimum:
                    raise SchemaError(cls, 'exclusive_minimum')
            else:
                if value < cls.minimum:
                    raise SchemaError(cls, 'minimum')

        if cls.maximum is not None:
            if cls.exclusive_maximum:
                if value >= cls.maximum:
                    raise SchemaError(cls, 'exclusive_maximum')
            else:
                if value > cls.maximum:
                    raise SchemaError(cls, 'maximum')

        if cls.multiple_of is not None:
            if isinstance(cls.multiple_of, float):
                failed = not (value * (1/cls.multiple_of)).is_integer()
            else:
                failed = value % cls.multiple_of
            if failed:
                raise SchemaError(cls, 'multiple_of')

        return value


class Number(_NumericType, float):
    native_type = float


class Integer(_NumericType, int):
    native_type = int


class Boolean(object):
    native_type = bool
    errors = {
        'type': 'Must be a valid boolean.'
    }

    def __new__(self, *args, **kwargs):
        assert len(args) == 1 and not kwargs
        value = args[0]

        if isinstance(value, str):
            try:
                return {
                    'true': True,
                    'false': False,
                    '1': True,
                    '0': False
                }[value.lower()]
            except KeyError:
                raise SchemaError(self, 'type')
        return bool(value)
