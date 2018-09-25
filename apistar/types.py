from abc import ABCMeta
from collections.abc import Mapping

from apistar import validators
from apistar.exceptions import ConfigurationError, ValidationError


class TypeMetaclass(ABCMeta):
    def __new__(cls, name, bases, attrs):
        properties = []
        for key, value in list(attrs.items()):
            if key in ['keys', 'items', 'values', 'get', 'validator']:
                msg = (
                    'Cannot use reserved name "%s" on Type "%s", as it '
                    'clashes with the class interface.'
                )
                raise ConfigurationError(msg % (key, name))

            elif hasattr(value, 'validate'):
                attrs.pop(key)
                properties.append((key, value))

        # If this class is subclassing another Type, add that Type's properties.
        # Note that we loop over the bases in reverse. This is necessary in order
        # to maintain the correct order of properties.
        for base in reversed(bases):
            if hasattr(base, 'validator'):
                properties = [
                    (key, base.validator.properties[key]) for key
                    in base.validator.properties
                    if key not in attrs
                ] + properties

        properties = sorted(
            properties,
            key=lambda item: item[1]._creation_counter
        )
        required = [
            key for key, value in properties
            if not value.has_default()
        ]

        attrs['validator'] = validators.Object(
            def_name=name,
            properties=properties,
            required=required,
            additional_properties=None
        )
        attrs['_creation_counter'] = validators.Validator._creation_counter
        validators.Validator._creation_counter += 1
        return super(TypeMetaclass, cls).__new__(cls, name, bases, attrs)

    def __subclasscheck__(cls, subclass):
        try:
            return ABCMeta.__subclasscheck__(cls, subclass)
        except TypeError:
            return False


class Type(Mapping, metaclass=TypeMetaclass):
    def __init__(self, *args, **kwargs):
        definitions = None
        allow_coerce = False

        if args:
            assert len(args) == 1
            definitions = kwargs.pop('definitions', definitions)
            allow_coerce = kwargs.pop('allow_coerce', allow_coerce)
            assert not kwargs

            if args[0] is None or isinstance(args[0], (bool, int, float, str, list)):
                raise ValidationError('Must be an object.')
            elif isinstance(args[0], dict):
                # Instantiated with a dict.
                value = args[0]
            else:
                # Instantiated with an object instance.
                value = {
                    key: getattr(args[0], key)
                    for key in self.validator.properties.keys()
                }
        else:
            # Instantiated with keyword arguments.
            value = kwargs

        value = self.validator.validate(value)
        object.__setattr__(self, '_dict', value)

    @classmethod
    def validate(cls, value, definitions=None, allow_coerce=False):
        return cls(value, definitions=definitions, allow_coerce=allow_coerce)

    @classmethod
    def has_default(cls):
        return False

    def __repr__(self):
        args = ['%s=%s' % (key, repr(value)) for key, value in self.items()]
        arg_string = ', '.join(args)
        return '<%s(%s)>' % (self.__class__.__name__, arg_string)

    def __setattr__(self, key, value):
        if key not in self._dict:
            raise AttributeError('Invalid attribute "%s"' % key)
        value = self.validator.properties[key].validate(value)
        self._dict[key] = value

    def __setitem__(self, key, value):
        if key not in self._dict:
            raise KeyError('Invalid key "%s"' % key)
        value = self.validator.properties[key].validate(value)
        self._dict[key] = value

    def __getattr__(self, key):
        try:
            return self._dict[key]
        except (KeyError,):
            raise AttributeError('Invalid attribute "%s"' % key)

    def __getitem__(self, key):
        value = self._dict[key]
        if value is None:
            return None
        validator = self.validator.properties[key]
        if hasattr(validator, 'format') and validator.format in validators.FORMATS:
            formatter = validators.FORMATS[validator.format]
            return formatter.to_string(value)
        return value

    def __len__(self):
        return len(self._dict)

    def __iter__(self):
        return iter(self._dict)
