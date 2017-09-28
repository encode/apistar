import math
import re
import typing

from apistar.exceptions import TypeSystemError


class String(str):
    native_type = str
    errors = {
        'blank': 'Must not be blank.',
        'max_length': 'Must have no more than {max_length} characters.',
        'min_length': 'Must have at least {min_length} characters.',
        'pattern': 'Must match the pattern /{pattern}/.',
        'input_type': 'Must be a valid {input_type}.',
    }
    max_length = None  # type: int
    min_length = None  # type: int
    pattern = None  # type: str
    input_type = None  # type: str
    trim_whitespace = True

    def __new__(cls, *args, **kwargs):
        value = super().__new__(cls, *args, **kwargs)

        if cls.trim_whitespace:
            value = value.strip()

        if cls.min_length is not None:
            if len(value) < cls.min_length:
                if cls.min_length == 1:
                    raise TypeSystemError(cls=cls, code='blank')
                else:
                    raise TypeSystemError(cls=cls, code='min_length')

        if cls.max_length is not None:
            if len(value) > cls.max_length:
                raise TypeSystemError(cls=cls, code='max_length')

        if cls.pattern is not None:
            if not re.search(cls.pattern, value):
                raise TypeSystemError(cls=cls, code='pattern')

        return value


class _NumericType(object):
    """
    Base class for both `Number` and `Integer`.
    """
    native_type = None  # type: type
    errors = {
        'type': 'Must be a valid number.',
        'finite': 'Must be a finite number.',
        'minimum': 'Must be greater than or equal to {minimum}.',
        'exclusive_minimum': 'Must be greater than {minimum}.',
        'maximum': 'Must be less than or equal to {maximum}.',
        'exclusive_maximum': 'Must be less than {maximum}.',
        'multiple_of': 'Must be a multiple of {multiple_of}.',
    }
    minimum = None  # type: typing.Union[float, int]
    maximum = None  # type: typing.Union[float, int]
    exclusive_minimum = False
    exclusive_maximum = False
    multiple_of = None  # type: typing.Union[float, int]

    def __new__(cls, *args, **kwargs):
        try:
            value = cls.native_type.__new__(cls, *args, **kwargs)
        except (TypeError, ValueError):
            raise TypeSystemError(cls=cls, code='type') from None

        if not math.isfinite(value):
            raise TypeSystemError(cls=cls, code='finite')

        if cls.minimum is not None:
            if cls.exclusive_minimum:
                if value <= cls.minimum:
                    raise TypeSystemError(cls=cls, code='exclusive_minimum')
            else:
                if value < cls.minimum:
                    raise TypeSystemError(cls=cls, code='minimum')

        if cls.maximum is not None:
            if cls.exclusive_maximum:
                if value >= cls.maximum:
                    raise TypeSystemError(cls=cls, code='exclusive_maximum')
            else:
                if value > cls.maximum:
                    raise TypeSystemError(cls=cls, code='maximum')

        if cls.multiple_of is not None:
            if isinstance(cls.multiple_of, float):
                failed = not (value * (1 / cls.multiple_of)).is_integer()
            else:
                failed = value % cls.multiple_of
            if failed:
                raise TypeSystemError(cls=cls, code='multiple_of')

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

    def __new__(cls, *args, **kwargs) -> bool:
        if args and isinstance(args[0], str):
            try:
                return {
                    'true': True,
                    'false': False,
                    'on': True,
                    'off': False,
                    '1': True,
                    '0': False,
                    '': False
                }[args[0].lower()]
            except KeyError:
                raise TypeSystemError(cls=cls, code='type') from None
        return bool(*args, **kwargs)


class Enum(str):
    errors = {
        'invalid': 'Must be a valid choice.',
    }
    enum = []  # type: typing.List[str]

    def __new__(cls, value: str):
        if value not in cls.enum:
            raise TypeSystemError(cls=cls, code='invalid')
        return value


class Object(dict):
    errors = {
        'type': 'Must be an object.',
        'invalid_key': 'Object keys must be strings.',
        'required': 'This field is required.',
    }
    properties = {}  # type: typing.Dict[str, typing.Any]
    required = []  # type: typing.List[str]

    def __init__(self, *args, **kwargs):
        if len(args) == 1 and not kwargs and isinstance(args[0], dict):
            value = args[0]
        else:
            try:
                value = dict(*args, **kwargs)
            except TypeError:
                if len(args) == 1 and not kwargs and hasattr(args[0], '__dict__'):
                    value = dict(args[0].__dict__)
                else:
                    raise TypeSystemError(cls=self.__class__, code='type') from None

        # Ensure all property keys are strings.
        errors = {}
        if any(not isinstance(key, str) for key in value.keys()):
            raise TypeSystemError(cls=self.__class__, code='invalid_key')

        # Properties
        for key, child_schema in self.properties.items():
            try:
                item = value[key]
            except KeyError:
                if hasattr(child_schema, 'default'):
                    # If a key is missing but has a default, then use that.
                    self[key] = child_schema.default
                elif key in self.required:
                    exc = TypeSystemError(cls=self.__class__, code='required')
                    errors[key] = exc.detail
            else:
                # Coerce value into the given schema type if needed.
                if isinstance(item, child_schema):
                    self[key] = item
                else:
                    try:
                        self[key] = child_schema(item)
                    except TypeSystemError as exc:
                        errors[key] = exc.detail

        if errors:
            raise TypeSystemError(errors)


class Array(list):
    errors = {
        'type': 'Must be a list.',
        'min_items': 'Not enough items.',
        'max_items': 'Too many items.',
        'unique_items': 'This item is not unique.',
    }
    items = None  # type: typing.Union[type, typing.List[type]]
    additional_items = False  # type: bool
    min_items = 0  # type: typing.Optional[int]
    max_items = None  # type: typing.Optional[int]
    unique_items = False  # type: bool

    def __init__(self, *args, **kwargs):
        if args and isinstance(args[0], (str, bytes)):
            raise TypeSystemError(cls=self.__class__, code='type')

        try:
            value = list(*args, **kwargs)
        except TypeError:
            raise TypeSystemError(cls=self.__class__, code='type') from None

        if isinstance(self.items, list) and len(self.items) > 1:
            if len(value) < len(self.items):
                raise TypeSystemError(cls=self.__class__, code='min_items')
            elif len(value) > len(self.items) and not self.additional_items:
                raise TypeSystemError(cls=self.__class__, code='max_items')

        if len(value) < self.min_items:
            raise TypeSystemError(cls=self.__class__, code='min_items')
        elif self.max_items is not None and len(value) > self.max_items:
            raise TypeSystemError(cls=self.__class__, code='max_items')

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
                        raise TypeSystemError(cls=self.__class__, code='unique_items')
                    else:
                        seen_items.add(item)

                self.append(item)
            except TypeSystemError as exc:
                errors[pos] = exc.detail

        if errors:
            raise TypeSystemError(errors)


def string(**kwargs) -> typing.Type:
    return type('String', (String,), kwargs)


def integer(**kwargs) -> typing.Type:
    return type('Integer', (Integer,), kwargs)


def number(**kwargs) -> typing.Type:
    return type('Number', (Number,), kwargs)


def boolean(**kwargs) -> typing.Type:
    return type('Boolean', (Boolean,), kwargs)


def enum(**kwargs) -> typing.Type:
    return type('Enum', (Enum,), kwargs)


def array(**kwargs) -> typing.Type:
    return type('Array', (Array,), kwargs)


def newtype(cls, **kwargs) -> typing.Type:
    return type(cls.__name__, (cls,), kwargs)
