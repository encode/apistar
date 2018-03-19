from abc import ABCMeta
from collections.abc import Mapping

from apistar import validators
from apistar.exceptions import ValidationError


class TypeMetaclass(ABCMeta):
    def __new__(cls, name, bases, attrs):
        properties = []
        required = []
        for key, value in list(attrs.items()):
            if isinstance(value, validators.Validator):
                attrs.pop(key)
                properties.append((key, value))
                if not value.has_default():
                    required.append(key)

        properties = sorted(
            properties,
            key=lambda item: item[1]._creation_counter
        )

        attrs['_validator'] = validators.Object(
            properties=properties,
            required=required,
            additional_properties=None
        )
        return super(TypeMetaclass, cls).__new__(cls, name, bases, attrs)


class Type(Mapping, metaclass=TypeMetaclass):
    def __init__(self, *args, **kwargs):
        if args:
            assert len(args) == 1
            arg = args[0]
            if arg is None or isinstance(arg, (bool, int, float, list)):
                raise ValidationError('Must be an object.')
            elif not isinstance(arg, dict):
                arg = {
                    key: getattr(arg, key)
                    for key in self._validator.properties.keys()
                }
        else:
            arg = kwargs

        value = self._validator.validate(arg)
        object.__setattr__(self, '_dict', value)

    def __repr__(self):
        args = ['%s=%s' % (key, repr(value)) for key, value in self.items()]
        arg_string = ', '.join(args)
        return '<%s(%s)>' % (self.__class__.__name__, arg_string)

    def __setattr__(self, key, value):
        if key not in self._dict:
            raise AttributeError('Invalid attribute "%s"' % key)
        value = self._validator.properties[key].validate(value)
        self._dict[key] = value

    def __setitem__(self, key, value):
        if key not in self._dict:
            raise KeyError('Invalid key "%s"' % key)
        value = self._validator.properties[key].validate(value)
        self._dict[key] = value

    def __getattr__(self, key):
        return self._dict[key]

    def __getitem__(self, key):
        value = self._dict[key]
        validator = self._validator.properties[key]
        if validator.format in validators.FORMATS:
            formatter = validators.FORMATS[validator.format]
            return formatter.to_string(value)
        return value

    def __len__(self):
        return len(self._dict)

    def __iter__(self):
        return iter(self._dict)
