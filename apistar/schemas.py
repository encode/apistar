from collections import OrderedDict
from typing import Dict, List, Tuple, Union
import re


# TODO: Validation errors
# TODO: allow_blank?


class _StringMetaclass(type):
    def __new__(cls, name, bases, namespace, **kwds):
        # If a pattern is included, then pre-compile the regex.
        pattern = bases[0].pattern if bases else None
        pattern = namespace.get('pattern', pattern)
        if pattern is not None:
            namespace['_pattern_regex'] = re.compile(pattern)
        else:
            namespace['_pattern_regex'] = None

        # Collect all errors from base classes
        if bases:
            errors = dict(bases[0].errors)
            errors.update(namespace.get('errors', {}))
            namespace['errors'] = errors

        # Add a base class for the 'String' class.
        if not bases:
            bases = (str,)

        return type.__new__(cls, name, bases, dict(namespace))


class String(metaclass=_StringMetaclass):
    errors = {
        'type': 'Must be a string.',
        'blank': 'Must not be blank.',
        'max_length': 'Must have no more than {max_length} characters.',
        'min_length': 'Must have at least {min_length} characters.',
        'pattern': 'Must match the pattern /{pattern}/.',
        'format': 'Must be a valid {format}.',
    }
    max_length = None  # type: int
    min_length = None  # type: int
    pattern = None  # type: str
    format = None  # type: str
    trim_whitespace = True

    def __new__(self, value=''):
        # TODO: Support initial native types if format is set.
        value = str.__new__(self, value)

        if self.trim_whitespace:
            value = value.strip()

        if self.min_length is not None:
            if len(value) < self.min_length:
                if self.min_length == 1:
                    msg = self.errors['blank']
                    raise ValueError(msg)
                else:
                    msg = self.errors['min_length'].format(
                        min_length=self.min_length
                    )
                    raise ValueError(msg)

        if self.max_length is not None:
            if len(value) > self.max_length:
                msg = self.errors['max_length'].format(
                    max_length=self.max_length
                )
                raise ValueError(msg)

        if self.pattern is not None:
            if not self._pattern_regex.search(value):
                msg = self.errors['pattern'].format(pattern=self.pattern)
                raise ValueError(msg)

        # TODO: 'format' validation, and storing native value

        return value

    def native(self):
        pass  # TODO


class _BaseNumberMetaclass(type):
    def __new__(cls, name, bases, namespace, **kwds):
        if bases:
            # Collect all errors from base classes.
            errors = dict(bases[0].errors)
            errors.update(namespace.get('errors', {}))
            namespace['errors'] = errors

        if namespace.get('_numeric_type') is not None:
            # Add a base class for Number and Integer.
            bases += (namespace['_numeric_type'],)

        return type.__new__(cls, name, bases, dict(namespace))


class _BaseNumber(metaclass=_BaseNumberMetaclass):
    _numeric_type = None  # type: type
    errors = {
        'type': 'Must be a number.',
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

    def __new__(self, value=0.0):
        value = self._numeric_type.__new__(self, value)

        if self.minimum is not None:
            if self.exclusive_minimum:
                if value <= self.minimum:
                    msg = self.errors['exclusive_minimum'].format(
                        minimum=self.minimum
                    )
                    raise ValueError(msg)
            else:
                if value < self.minimum:
                    msg = self.errors['minimum'].format(
                        minimum=self.minimum
                    )
                    raise ValueError(msg)

        if self.maximum is not None:
            if self.exclusive_maximum:
                if value >= self.maximum:
                    msg = self.errors['exclusive_maximum'].format(
                        maximum=self.maximum
                    )
                    raise ValueError(msg)
            else:
                if value > self.maximum:
                    msg = self.errors['maximum'].format(
                        maximum=self.maximum
                    )
                    raise ValueError(msg)

        if self.multiple_of is not None:
            if isinstance(self.multiple_of, float):
                failed = not (float(value) / self.multiple_of).is_integer()
            else:
                failed = value % self.multiple_of
            if failed:
                msg = self.errors['multiple_of'].format(
                    multiple_of=self.multiple_of
                )
                raise ValueError(msg)

        return value


class Integer(_BaseNumber):
    _numeric_type = int


class Number(_BaseNumber):
    _numeric_type = float


class Boolean(object):
    def __new__(self, value=False):
        if isinstance(value, str):
            try:
                return {
                    'true': True,
                    'false': False,
                    '1': True,
                    '0': False
                }[value.lower()]
            except KeyError:
                pass
        return bool(value)


class _ObjectMetaclass(type):
    def __new__(cls, name, bases, namespace, **kwds):
        # If a pattern is included, then pre-compile the regex.
        pattern_properties = bases[0].pattern_properties if bases else None
        pattern_properties = namespace.get('pattern_properties', pattern_properties)
        if pattern_properties is not None:
            namespace['_pattern_properties_regex'] = {
                re.compile(key): value
                for key, value
                in pattern_properties.items()
            }
        else:
            namespace['_pattern_properties_regex'] = None

        if bases:
            # Collect all errors from base classes.
            errors = dict(bases[0].errors)
            errors.update(namespace.get('errors', {}))
            namespace['errors'] = errors

        if isinstance(namespace.get('properties'), list):
            # A list of tuples can be used as shortcut for an ordered dict.
            namespace['properties'] = OrderedDict(namespace['properties'])

        if not bases:
            # Add a base class for Object.
            bases += (dict,)

        return type.__new__(cls, name, bases, dict(namespace))


class Object(metaclass=_ObjectMetaclass):
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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # When named keyword arguments are used, we default
        # to raising errors on unknown properties.
        additional_properties = self.additional_properties
        if additional_properties is None and kwargs:
            additional_properties = False

        errors = {}
        if any(not isinstance(key, str) for key in self.keys()):
            errors[''] = self.errors['invalid_key']

        if self.required is not None:
            for key in self.required:
                if key not in self:
                    errors[key] = self.errors['required']

        if self.min_properties is not None:
            if len(self) < self.min_properties:
                if self.min_properties == 1:
                    errors[''] = self.errors('empty')
                else:
                    errors[''] = self.errors['min_properties'].format(
                        min_properties=self.min_properties
                    )

        if self.max_properties is not None:
            if len(self) > self.max_properties:
                errors[''] = self.errors['max_properties'].format(
                    max_properties=self.max_properties
                )

        # Properties
        remaining_keys = set(self.keys())
        if self.properties is not None:
            remaining_keys -= set(self.properties.keys())
            for key, schema in self.properties.items():
                if key not in self:
                    continue
                item = self[key]
                if isinstance(item, schema):
                    continue
                self[key] = schema(self[key])

        # Pattern properties
        if self.pattern_properties is not None:
            for key in list(remaining_keys):
                for pattern, schema in self._pattern_properties_regex.items():
                    if re.search(pattern, key):
                        self[key] = schema(self[key])
                        remaining_keys.discard(key)

        # Additional properties
        if isinstance(additional_properties, type):
            for key in remaining_keys:
                self[key] = additional_properties(self[key])
        elif additional_properties is False:
            for key in remaining_keys:
                errors[key] = self.errors['invalid_property']
        elif additional_properties is None:
            for key in remaining_keys:
                self.pop(key)

        if errors:
            raise TypeError(errors)

    def ordered(self):
        """
        Returns an OrderedDict representation of this object,
        with keys sorted by their 'properties' ordering.
        """
        ordering = list(self.properties.keys() or [])
        def key(pair):
            if pair[0] in ordering:
                return (0, ordering.index(pair[0]))
            return (1, pair[0])
        pairs = [
            (key, value.ordered()) if hasattr(value, 'ordered') else (key, value)
            for key, value in self.items()
        ]
        return OrderedDict(sorted(pairs, key=key))


def Type(schema, **kwargs) -> type:
    return type(schema.__name__, (schema,), kwargs)


class Username(String):
    errors = {
        'pattern': 'Username may only contain letters, numbers, and underscores.',
        'blank': 'May not be blank.',
    }
    pattern = r'^[A-Za-z0-9_]+$'
    min_length = 1


class Score(Number):
    minimum = 0


class User(Object):
    properties = [
        ('username', Username),
        ('is_active', Boolean),
        ('score', Score),
        ('age', Type(Integer, maximum=10))
    ]
    pattern_properties = {
        '^x_': Type(String, min_length=1, max_length=10)
    }


u = User(
    username='tomchrdgfg35istie',
    is_active=Boolean('true'),
    score=Score(3),
    age=9,
    x_extra='sdf'
)

import json
print(json.dumps(u.ordered(), indent=4))
#print(json.dumps(u, indent=4))
#print(type(u['score']))
