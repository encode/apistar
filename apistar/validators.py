import re
import typing
from math import isfinite

from apistar import formats
from apistar.compat import dict_type
from apistar.exceptions import ValidationError

NO_DEFAULT = object()

FORMATS = {
    'date': formats.DateFormat(),
    'time': formats.TimeFormat(),
    'datetime': formats.DateTimeFormat()
}


class ErrorMessage(str):
    def __new__(cls, message, code):
        instance = str.__new__(cls, message)
        instance.code = code
        return instance


class Validator:
    errors = {}
    _creation_counter = 0

    def __init__(self, title='', description='', default=NO_DEFAULT, allow_null=False, definitions=None, def_name=None):
        definitions = {} if (definitions is None) else dict_type(definitions)

        assert isinstance(title, str)
        assert isinstance(description, str)
        assert isinstance(definitions, dict)
        assert all(isinstance(k, str) for k in definitions.keys())
        assert all(isinstance(v, Validator) for v in definitions.values())

        if allow_null and default is NO_DEFAULT:
            default = None

        if default is not NO_DEFAULT:
            self.default = default

        self.title = title
        self.description = description
        self.allow_null = allow_null
        self.definitions = definitions
        self.def_name = def_name

        # We need this global counter to determine what order fields have
        # been declared in when used with `Type`.
        self._creation_counter = Validator._creation_counter
        Validator._creation_counter += 1

    def validate(self, value, definitions=None, allow_coerce=False):
        raise NotImplementedError()

    def is_valid(self, value):
        try:
            self.validate(value)
        except ValidationError:
            return False
        return True

    def has_default(self):
        return hasattr(self, 'default')

    def error(self, code, **context):
        message = self.error_message(code, **context)
        raise ValidationError(message)

    def error_message(self, code, **context):
        message = self.errors[code].format(**self.__dict__, **context)
        return ErrorMessage(message, code)

    def get_definitions(self, definitions=None):
        if self.definitions is None and self.def_name is None:
            return definitions

        if definitions is None:
            definitions = {}
        if self.definitions is not None:
            definitions.update(self.definitions)
        if self.def_name is not None:
            definitions[self.def_name] = self
        return definitions

    def __or__(self, other):
        if isinstance(self, Union):
            items = self.items
        else:
            items = [self]

        if isinstance(other, Union):
            items += other.items
        else:
            items += [other]

        return Union(items)


class String(Validator):
    errors = {
        'type': 'Must be a string.',
        'null': 'May not be null.',
        'blank': 'Must not be blank.',
        'max_length': 'Must have no more than {max_length} characters.',
        'min_length': 'Must have at least {min_length} characters.',
        'pattern': 'Must match the pattern /{pattern}/.',
        'format': 'Must be a valid {format}.',
        'enum': 'Must be one of {enum}.',
        'exact': 'Must be {exact}.'
    }

    def __init__(self, max_length=None, min_length=None, pattern=None,
                 enum=None, format=None, **kwargs):
        super().__init__(**kwargs)

        assert max_length is None or isinstance(max_length, int)
        assert min_length is None or isinstance(min_length, int)
        assert pattern is None or isinstance(pattern, str)
        assert enum is None or isinstance(enum, list) and all([isinstance(i, str) for i in enum])
        assert format is None or isinstance(format, str)

        self.max_length = max_length
        self.min_length = min_length
        self.pattern = pattern
        self.enum = enum
        self.format = format

    def validate(self, value, definitions=None, allow_coerce=False):
        if value is None and self.allow_null:
            return None
        elif value is None:
            self.error('null')
        elif self.format in FORMATS and FORMATS[self.format].is_native_type(value):
            return value
        elif not isinstance(value, str):
            self.error('type')

        if self.enum is not None:
            if value not in self.enum:
                if len(self.enum) == 1:
                    self.error('exact', exact=self.enum[0])
                self.error('enum')

        if self.min_length is not None:
            if len(value) < self.min_length:
                if self.min_length == 1:
                    self.error('blank')
                else:
                    self.error('min_length')

        if self.max_length is not None:
            if len(value) > self.max_length:
                self.error('max_length')

        if self.pattern is not None:
            if not re.search(self.pattern, value):
                self.error('pattern')

        if self.format in FORMATS:
            return FORMATS[self.format].validate(value)

        return value


class NumericType(Validator):
    """
    Base class for both `Number` and `Integer`.
    """
    numeric_type = None  # type: type
    errors = {
        'type': 'Must be a number.',
        'null': 'May not be null.',
        'integer': 'Must be an integer.',
        'finite': 'Must be finite.',
        'minimum': 'Must be greater than or equal to {minimum}.',
        'exclusive_minimum': 'Must be greater than {minimum}.',
        'maximum': 'Must be less than or equal to {maximum}.',
        'exclusive_maximum': 'Must be less than {maximum}.',
        'multiple_of': 'Must be a multiple of {multiple_of}.',
        'enum': 'Must be one of {enum}.',
        'exact': 'Must be {exact}.'
    }

    def __init__(self, minimum=None, maximum=None, exclusive_minimum=False,
                 exclusive_maximum=False, multiple_of=None, enum=None,
                 format=None, **kwargs):
        super().__init__(**kwargs)

        assert minimum is None or isinstance(minimum, (int, float))
        assert maximum is None or isinstance(maximum, (int, float))
        assert isinstance(exclusive_minimum, bool)
        assert isinstance(exclusive_maximum, bool)
        assert multiple_of is None or isinstance(multiple_of, (int, float))
        assert enum is None or isinstance(enum, list) and all([isinstance(i, str) for i in enum])
        assert format is None or isinstance(format, str)

        self.minimum = minimum
        self.maximum = maximum
        self.exclusive_minimum = exclusive_minimum
        self.exclusive_maximum = exclusive_maximum
        self.multiple_of = multiple_of
        self.enum = enum
        self.format = format

    def validate(self, value, definitions=None, allow_coerce=False):
        if value is None and self.allow_null:
            return None
        elif value is None:
            self.error('null')
        elif isinstance(value, bool):
            self.error('type')
        elif self.numeric_type is int and isinstance(value, float) and not value.is_integer():
            self.error('integer')
        elif not isinstance(value, (int, float)) and not allow_coerce:
            self.error('type')
        elif isinstance(value, float) and not isfinite(value):
            self.error('finite')

        try:
            value = self.numeric_type(value)
        except (TypeError, ValueError):
            self.error('type')

        if self.enum is not None:
            if value not in self.enum:
                if len(self.enum) == 1:
                    self.error('exact', exact=self.enum[0])
                self.error('enum')

        if self.minimum is not None:
            if self.exclusive_minimum:
                if value <= self.minimum:
                    self.error('exclusive_minimum')
            else:
                if value < self.minimum:
                    self.error('minimum')

        if self.maximum is not None:
            if self.exclusive_maximum:
                if value >= self.maximum:
                    self.error('exclusive_maximum')
            else:
                if value > self.maximum:
                    self.error('maximum')

        if self.multiple_of is not None:
            if isinstance(self.multiple_of, float):
                if not (value * (1 / self.multiple_of)).is_integer():
                    self.error('multiple_of')
            else:
                if value % self.multiple_of:
                    self.error('multiple_of')

        return value


class Number(NumericType):
    numeric_type = float


class Integer(NumericType):
    numeric_type = int


class Boolean(Validator):
    errors = {
        'type': 'Must be a valid boolean.',
        'null': 'May not be null.',
    }
    values = {
        'true': True,
        'false': False,
        'on': True,
        'off': False,
        '1': True,
        '0': False,
        '': False,
    }
    null_values = {
        '': None,
        'null': None,
        'none': None,
    }

    def validate(self, value, definitions=None, allow_coerce=False):
        if value is None and self.allow_null:
            return None

        elif value is None:
            self.error('null')

        elif not isinstance(value, bool):
            if allow_coerce and isinstance(value, str):
                if self.allow_null:
                    values = dict(self.value)
                    values.update(self.null_values)
                else:
                    values = self.values
                try:
                    return values[value.lower()]
                except KeyError:
                    pass
            self.error('type')

        return value


class Object(Validator):
    errors = {
        'type': 'Must be an object.',
        'null': 'May not be null.',
        'invalid_key': 'Object keys must be strings.',
        'required': 'The "{field_name}" field is required.',
        'invalid_property': 'Invalid property name.',
        'empty': 'Must not be empty.',
        'max_properties': 'Must have no more than {max_properties} properties.',
        'min_properties': 'Must have at least {min_properties} properties.',
    }

    def __init__(self, properties=None, pattern_properties=None,
                 additional_properties=True, min_properties=None,
                 max_properties=None, required=None,
                 **kwargs):
        super().__init__(**kwargs)

        properties = {} if (properties is None) else dict_type(properties)
        pattern_properties = {} if (pattern_properties is None) else dict_type(pattern_properties)
        required = list(required) if isinstance(required, (list, tuple)) else required
        required = [] if (required is None) else required

        assert all(isinstance(k, str) for k in properties.keys())
        assert all(hasattr(v, 'validate') for v in properties.values())
        assert all(isinstance(k, str) for k in pattern_properties.keys())
        assert all(hasattr(v, 'validate') for v in pattern_properties.values())
        assert additional_properties in (None, True, False) or hasattr(additional_properties, 'validate')
        assert min_properties is None or isinstance(min_properties, int)
        assert max_properties is None or isinstance(max_properties, int)
        assert all(isinstance(i, str) for i in required)

        self.properties = properties
        self.pattern_properties = pattern_properties
        self.additional_properties = additional_properties
        self.min_properties = min_properties
        self.max_properties = max_properties
        self.required = required

    def validate(self, value, definitions=None, allow_coerce=False):
        if value is None and self.allow_null:
            return None
        elif value is None:
            self.error('null')
        elif not isinstance(value, (dict, typing.Mapping)):
            self.error('type')

        definitions = self.get_definitions(definitions)
        validated = dict_type()

        # Ensure all property keys are strings.
        errors = {}
        for key in value.keys():
            if not isinstance(key, str):
                errors[key] = self.error_message('invalid_key')

        # Min/Max properties
        if self.min_properties is not None:
            if len(value) < self.min_properties:
                if self.min_properties == 1:
                    self.error('empty')
                else:
                    self.error('min_properties')
        if self.max_properties is not None:
            if len(value) > self.max_properties:
                self.error('max_properties')

        # Required properties
        for key in self.required:
            if key not in value:
                errors[key] = self.error_message('required', field_name=key)

        # Properties
        for key, child_schema in self.properties.items():
            if key not in value:
                if child_schema.has_default():
                    validated[key] = child_schema.default
                continue
            item = value[key]
            try:
                validated[key] = child_schema.validate(
                    item,
                    definitions=definitions,
                    allow_coerce=allow_coerce
                )
            except ValidationError as exc:
                errors[key] = exc.detail

        # Pattern properties
        if self.pattern_properties:
            for key in list(value.keys()):
                for pattern, child_schema in self.pattern_properties.items():
                    if isinstance(key, str) and re.search(pattern, key):
                        item = value[key]
                        try:
                            validated[key] = child_schema.validate(
                                item, definitions=definitions,
                                allow_coerce=allow_coerce
                            )
                        except ValidationError as exc:
                            errors[key] = exc.detail

        # Additional properties
        remaining = [
            key for key in value.keys()
            if key not in set(validated.keys()) | set(errors.keys())
        ]

        if self.additional_properties is True:
            for key in remaining:
                validated[key] = value[key]
        elif self.additional_properties is False:
            for key in remaining:
                errors[key] = self.error_message('invalid_property')
        elif self.additional_properties is not None:
            child_schema = self.additional_properties
            for key in remaining:
                item = value[key]
                try:
                    validated[key] = child_schema.validate(
                        item,
                        definitions=definitions,
                        allow_coerce=allow_coerce
                    )
                except ValidationError as exc:
                    errors[key] = exc.detail

        if errors:
            raise ValidationError(errors)

        return validated


class Array(Validator):
    errors = {
        'type': 'Must be an array.',
        'null': 'May not be null.',
        'empty': 'Must not be empty.',
        'exact_items': 'Must have {min_items} items.',
        'min_items': 'Must have at least {min_items} items.',
        'max_items': 'Must have no more than {max_items} items.',
        'additional_items': 'May not contain additional items.',
        'unique_items': 'This item is not unique.',
    }

    def __init__(self, items=None, additional_items=None, min_items=None,
                 max_items=None, unique_items=False, **kwargs):
        super().__init__(**kwargs)

        items = list(items) if isinstance(items, (list, tuple)) else items

        assert items is None or hasattr(items, 'validate') or (
            isinstance(items, list) and
            all(hasattr(i, 'validate') for i in items)
        )
        assert additional_items in (None, True, False) or hasattr(additional_items, 'validate')
        assert min_items is None or isinstance(min_items, int)
        assert max_items is None or isinstance(max_items, int)
        assert isinstance(unique_items, bool)

        self.items = items
        self.additional_items = additional_items
        self.min_items = min_items
        self.max_items = max_items
        self.unique_items = unique_items

    def validate(self, value, definitions=None, allow_coerce=False):
        if value is None and self.allow_null:
            return None
        elif value is None:
            self.error('null')
        elif not isinstance(value, list):
            self.error('type')

        definitions = self.get_definitions(definitions)
        validated = []

        if self.min_items is not None and self.min_items == self.max_items and len(value) != self.min_items:
            self.error('exact_items')
        if self.min_items is not None and len(value) < self.min_items:
            if self.min_items == 1:
                self.error('empty')
            self.error('min_items')
        elif self.max_items is not None and len(value) > self.max_items:
            self.error('max_items')
        elif isinstance(self.items, list) and (self.additional_items is False) and len(value) > len(self.items):
            self.error('additional_items')

        # Ensure all items are of the right type.
        errors = {}
        if self.unique_items:
            seen_items = Uniqueness()

        for pos, item in enumerate(value):
            try:
                if isinstance(self.items, list):
                    if pos < len(self.items):
                        item = self.items[pos].validate(
                            item,
                            definitions=definitions,
                            allow_coerce=allow_coerce
                        )
                    elif isinstance(self.additional_items, Validator):
                        item = self.additional_items.validate(
                            item,
                            definitions=definitions,
                            allow_coerce=allow_coerce
                        )
                elif self.items is not None:
                    item = self.items.validate(
                        item,
                        definitions=definitions,
                        allow_coerce=allow_coerce
                    )

                if self.unique_items:
                    if item in seen_items:
                        self.error('unique_items')
                    else:
                        seen_items.add(item)

                validated.append(item)
            except ValidationError as exc:
                errors[pos] = exc.detail

        if errors:
            raise ValidationError(errors)

        return validated


class Date(String):
    def __init__(self, **kwargs):
        super().__init__(format='date', **kwargs)


class Time(String):
    def __init__(self, **kwargs):
        super().__init__(format='time', **kwargs)


class DateTime(String):
    def __init__(self, **kwargs):
        super().__init__(format='datetime', **kwargs)


class Any(Validator):
    def validate(self, value, definitions=None, allow_coerce=False):
        # TODO: Validate value matches primitive types
        return value


class Union(Validator):
    errors = {
        'null': 'Must not be null.',
        'union': 'Must match one of the union types.'
    }

    def __init__(self, items, **kwargs):
        super().__init__(**kwargs)
        assert isinstance(items, list) and all(isinstance(i, Validator) for i in items)
        self.items = list(items)

    def validate(self, value, definitions=None, allow_coerce=False):
        if value is None and self.allow_null:
            return None
        elif value is None:
            self.error('null')

        for item in self.items:
            try:
                return item.validate(
                    value,
                    definitions=definitions,
                    allow_coerce=allow_coerce
                )
            except ValidationError:
                pass
        self.error('union')


class Ref(Validator):
    def __init__(self, ref, **kwargs):
        super().__init__(**kwargs)
        assert isinstance(ref, str)
        self.ref = ref

    def validate(self, value, definitions=None, allow_coerce=False):
        assert definitions is not None, 'Ref.validate() requires definitions'
        assert self.ref in definitions, 'Ref "%s" not in definitions' % self.ref

        child_schema = definitions[self.ref]
        return child_schema.validate(
            value,
            definitions=definitions,
            allow_coerce=allow_coerce
        )


class Uniqueness():
    """
    A set-like class that tests for uniqueness of primitive types.

    Ensures the `True` and `False` are treated as distinct from `1` and `0`,
    and coerces non-hashable instances that cannot be added to sets,
    into hashable representations that can.
    """
    TRUE = object()
    FALSE = object()

    def __init__(self):
        self._set = set()

    def __contains__(self, item):
        item = self.make_hashable(item)
        return item in self._set

    def add(self, item):
        item = self.make_hashable(item)
        self._set.add(item)

    def make_hashable(self, element):
        """
        Coerce a primitive into a uniquely hashable type, for uniqueness checks.
        """

        # Only primitive types can be handled.
        assert (element is None) or isinstance(element, (bool, int, float, str, list, dict))

        if element is True:
            # Need to make `True` distinct from `1`.
            return self.TRUE
        elif element is False:
            # Need to make `False` distinct from `0`.
            return self.FALSE
        elif isinstance(element, list):
            # Represent lists using a two-tuple of ('list', (item, item, ...))
            return ('list', tuple([
                self.make_hashable(item) for item in element
            ]))
        elif isinstance(element, dict):
            # Represent dicts using a two-tuple of ('dict', ((key, val), (key, val), ...))
            return ('dict', tuple([
                (self.make_hashable(key), self.make_hashable(value)) for key, value in element.items()
            ]))

        return element
