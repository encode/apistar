import re
from typing import Any, Dict, List, Optional, Tuple, Union, overload  # noqa

from apistar.exceptions import SchemaError, ValidationError


# TODO: Error on unknown attributes
# TODO: allow_blank?
# TODO: format (check type at start and allow, coerce, .native)
# TODO: default=empty
# TODO: check 'required' exists in 'properties'
# TODO: smarter ordering
# TODO: extra_properties=False by default
# TODO: inf, -inf, nan
# TODO: Overriding errors
# TODO: Blank booleans as False?


def validate(schema: type, value: Any, key=None):
    try:
        return schema(value)
    except SchemaError as exc:
        if key is None:
            detail = exc.detail
        else:
            detail = {key: exc.detail}
        raise ValidationError(detail=detail)


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
        value = super().__new__(cls, *args)

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

    # The following is currently required in order to keep mypy happy
    # with our atypical usage of `__new__`...
    # See: https://github.com/python/mypy/issues/3307

    def __init__(self, *args, **kwargs):  # pragma: nocover
        super().__init__()


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
                failed = not (value * (1 / cls.multiple_of)).is_integer()
            else:
                failed = value % cls.multiple_of
            if failed:
                raise SchemaError(error_message(cls, 'multiple_of'))

        return value

    # The following is currently required in order to keep mypy happy
    # with our atypical usage of `__new__`...
    # See: https://github.com/python/mypy/issues/3307

    def __init__(self, *args, **kwargs):
        super().__init__()


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
        'required': 'This field is required.',
    }
    properties = {}  # type: Dict[str, Any]

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
            if hasattr(value, '__dict__'):
                value = dict(value.__dict__)
            else:
                raise SchemaError(error_message(self, 'type'))

        # Ensure all property keys are strings.
        errors = {}
        if any(not isinstance(key, str) for key in value.keys()):
            raise SchemaError(error_message(self, 'invalid_key'))

        # Properties
        for key, child_schema in self.properties.items():
            try:
                item = value[key]
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


class Array(list):
    errors = {
        'type': 'Must be a list.',
        'min_items': 'Not enough items.',
        'max_items': 'Too many items.',
        'unique_items': 'This item is not unique.',
    }
    items = None  # type: Union[type, List[type]]
    additional_items = False  # type: bool
    min_items = 0  # type: Optional[int]
    max_items = None  # type: Optional[int]
    unique_items = False  # type: bool

    def __new__(cls, *args, **kwargs):
        if kwargs:
            assert not args
            return type(cls.__name__, (cls,), kwargs)

        assert len(args) == 1
        return list.__new__(cls, *args)

    def __init__(self, value):
        try:
            value = list(value)
        except TypeError:
            raise SchemaError(error_message(self, 'type'))

        if isinstance(self.items, list) and len(self.items) > 1:
            if len(value) < len(self.items):
                raise SchemaError(error_message(self, 'min_items'))
            elif len(value) > len(self.items) and not self.additional_items:
                raise SchemaError(error_message(self, 'max_items'))

        if len(value) < self.min_items:
            raise SchemaError(error_message(self, 'min_items'))
        elif self.max_items is not None and len(value) > self.max_items:
            raise SchemaError(error_message(self, 'max_items'))

        # Ensure all items are of the right type.
        errors = {}
        if self.unique_items:
            seen_items = set()

        for pos, item in enumerate(value):
            try:
                if isinstance(self.items, list):
                    if pos < len(self.items):
                        item = self.items[pos](item)
                elif self.items is not None:
                    item = self.items(item)

                if self.unique_items:
                    if item in seen_items:
                        raise SchemaError(error_message(self, 'unique_items'))
                    else:
                        seen_items.add(item)

                self.append(item)
            except SchemaError as exc:
                errors[pos] = exc.detail

        if errors:
            raise SchemaError(errors)
