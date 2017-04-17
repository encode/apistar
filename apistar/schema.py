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

    def native(self):
        pass  # TODO


class _NumericType(object):
    """
    Base class for both `Number` and `Integer`.
    """
    _numeric_type = None  # type: type
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
            value = cls._numeric_type.__new__(cls, value)
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
    _numeric_type = float


class Integer(_NumericType, int):
    _numeric_type = int


class Boolean(object):
    errors = {
        'type': 'Must be a valid boolean.'
    }

    def __new__(self, *args, **kwargs):
        if kwargs:
            assert not args
            return type(self.__name__, (self,), kwargs)

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
                raise SchemaError(self, 'type')
        return bool(value)


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
    properties = None  # type: Union[Dict[str, type], List[Tuple[str, type]]]
    required = None  # type: list
    max_properties = None  # type: int
    min_properties = None  # type: int
    pattern_properties = None  # type: Dict[str, type]
    additional_properties = None  # type: Union[bool, type]

    def __new__(cls, *args, **kwargs):
        if kwargs:
            assert not args
            return type(cls.__name__, (cls,), kwargs)

        assert len(args) == 1
        return dict.__new__(cls, *args)

    def __init__(self, value):
        value = dict(value)

        # Ensure all property keys are strings.
        errors = {}
        if any(not isinstance(key, str) for key in value.keys()):
            errors[''] = self.errors['invalid_key']

        # Enforce any required properties.
        if self.required is not None:
            for key in self.required:
                if key not in value:
                    errors[key] = self.errors['required']

        # Ensure object has at least 'min_properties'
        if self.min_properties is not None:
            if len(value) < self.min_properties:
                if self.min_properties == 1:
                    errors[''] = self.errors('empty')
                else:
                    errors[''] = self.errors['min_properties'].format(
                        min_properties=self.min_properties
                    )

        # Ensure object has at no more than 'max_properties'
        if self.max_properties is not None:
            if len(value) > self.max_properties:
                errors[''] = self.errors['max_properties'].format(
                    max_properties=self.max_properties
                )

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
                    # Coerce value into the given schema type if needed.
                    if isinstance(item, child_schema):
                        self[key] = item
                    else:
                        self[key] = child_schema(item)

        # Pattern properties
        if self.pattern_properties is not None:
            for pattern, child_schema in self.pattern_properties.items():
                for key in list(value.keys()):
                    if re.search(pattern, key):
                        # Set the value, coerceing into the required schema if needed.
                        item = value.pop(key)
                        if isinstance(item, child_schema):
                            self[key] = item
                        else:
                            self[key] = child_schema(item)

        # Additional properties
        if self.additional_properties is not None:
            if self.additional_properties is True:
                # Allow additional properties
                for key, item in value.items():
                    self[key] = item
            elif self.additional_properties is False:
                # Disallow additional properties
                for key in value.keys():
                    errors[key] = self.errors['invalid_property']
            elif isinstance(self.additional_properties, type):
                # Allow additional properties, enforcing a schema
                child_schema = self.additional_properties
                for key, item in value.items():
                    if isinstance(item, child_schema):
                        self[key] = item
                    else:
                        self[key] = child_schema(item)

        if errors:
            raise SchemaError(errors)
