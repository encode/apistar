import re
from typing import Any, Dict, List, Tuple, Type, Union  # noqa

from apistar.exceptions import SchemaError, ValidationError


# TODO: Error on unknown attributes
# TODO: allow_blank?
# TODO: format (check type at start and allow, coerce, .native)
# TODO: Array
# TODO: default=empty
# TODO: check 'required' exists in 'properties'
# TODO: smarter ordering
# TODO: extra_properties=False by default
# TODO: inf, -inf, nan
# TODO: Overriding errors
# TODO: Blank booleans as False?


def validate(schema: type, value: Any):
    try:
        return schema(value)
    except SchemaError as exc:
        raise ValidationError(detail=exc.detail)


def error_message(schema, code):
    return schema.errors[code].format(**schema.__dict__)


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
        if kwargs:
            assert not args
            return type(cls.__name__, (cls,), kwargs)

        assert len(args) == 1
        value = str.__new__(cls, *args)

        if cls.trim_whitespace:
            value = value.strip()

        if cls.min_length is not None:
            if len(value) < cls.min_length:
                if cls.min_length == 1:
                    raise SchemaError(error_message(cls, 'blank'))
                else:
                    raise SchemaError(error_message(cls, 'min_length'))

        if cls.max_length is not None:
            if len(value) > cls.max_length:
                raise SchemaError(error_message(cls, 'max_length'))

        if cls.pattern is not None:
            if not re.search(cls.pattern, value):
                raise SchemaError(error_message(cls, 'pattern'))

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
        if kwargs:
            assert not args
            return type(cls.__name__, (cls,), kwargs)

        assert len(args) == 1
        value = args[0]
        try:
            value = cls.native_type.__new__(cls, value)
        except (TypeError, ValueError):
            raise SchemaError(error_message(cls, 'type'))

        if cls.minimum is not None:
            if cls.exclusive_minimum:
                if value <= cls.minimum:
                    raise SchemaError(error_message(cls, 'exclusive_minimum'))
            else:
                if value < cls.minimum:
                    raise SchemaError(error_message(cls, 'minimum'))

        if cls.maximum is not None:
            if cls.exclusive_maximum:
                if value >= cls.maximum:
                    raise SchemaError(error_message(cls, 'exclusive_maximum'))
            else:
                if value > cls.maximum:
                    raise SchemaError(error_message(cls, 'maximum'))

        if cls.multiple_of is not None:
            if isinstance(cls.multiple_of, float):
                failed = not (value * (1/cls.multiple_of)).is_integer()
            else:
                failed = value % cls.multiple_of
            if failed:
                raise SchemaError(error_message(cls, 'multiple_of'))

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

    def __new__(cls, *args, **kwargs):
        if kwargs:
            assert not args
            return type(cls.__name__, (cls,), kwargs)

        assert len(args) == 1
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
                raise SchemaError(error_message(cls, 'type'))
        return bool(value)


class Enum(str):
    errors = {
        'enum': 'Must be a valid choice.',
        'exact': 'Must be {exact}.'
    }
    enum = []  # type: List[str]

    def __new__(cls, *args, **kwargs):
        if kwargs:
            assert not args
            return type(cls.__name__, (cls,), kwargs)

        assert len(args) == 1
        value = args[0]

        if value not in cls.enum:
            if len(cls.enum) == 1:
                raise SchemaError(error_message(cls, 'exact'))
            raise SchemaError(error_message(cls, 'enum'))
        return value


class Object(dict):
    errors = {
        'type': 'Must be an object.',
        'invalid_key': 'Object keys must be strings.',
        'empty': 'Must not be empty.',
        'required': 'This field is required.',
        'max_properties': 'Must have no more than {max_properties} properties.',
        'min_properties': 'Must have at least {min_properties} properties.',
        'invalid_property': 'Invalid property.'
    }
    properties = None  # type: Dict[str, type]
    required = None  # type: List[str]

    def __new__(cls, *args, **kwargs):
        if kwargs:
            assert not args
            return type(cls.__name__, (cls,), kwargs)

        assert len(args) == 1
        return dict.__new__(cls, *args)

    def __init__(self, value):
        try:
            value = dict(value)
        except TypeError:
            raise SchemaError(error_message(self, 'type'))

        # Ensure all property keys are strings.
        errors = {}
        if any(not isinstance(key, str) for key in value.keys()):
            raise SchemaError(error_message(self, 'invalid_key'))

        # Enforce any required properties.
        if self.required is not None:
            for key in self.required:
                if key not in value:
                    errors[key] = error_message(self, 'required')

        # Properties
        if self.properties is not None:
            for key, child_schema in self.properties.items():
                try:
                    item = value.pop(key)
                except KeyError:
                    if hasattr(child_schema, 'default'):
                        # If a key is missing but has a default, then use that.
                        self[key] = child_schema.default
                    else:
                        errors[key] = error_message(self, 'required')

                else:
                    # Coerce value into the given schema type if needed.
                    if isinstance(item, child_schema):
                        self[key] = item
                    else:
                        try:
                            self[key] = child_schema(item)
                        except SchemaError as exc:
                            errors[key] = exc.detail

        if errors:
            raise SchemaError(errors)
