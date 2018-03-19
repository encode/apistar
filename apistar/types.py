from apistar import validators
from apistar.compat import dict_type


class TypeMetaclass(type):
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


class Type(dict_type, metaclass=TypeMetaclass):
    def __init__(self, *args, **kwargs):
        if args:
            assert len(args) == 1
            validated = self._validator.validate(args[0])
        else:
            validated = self._validator.validate(kwargs)
        for key, value in validated.items():
            dict_type.__setitem__(self, key, value)

    def __repr__(self):
        args = ['%s=%s' % (key, repr(value)) for key, value in self.items()]
        arg_string = ', '.join(args)
        return '<%s(%s)>' % (self.__class__.__name__, arg_string)

    def __setattr__(self, key, value):
        if key not in self._validator.properties:
            raise AttributeError('Invalid attribute "%s"' % key)
        self[key] = value

    def __setitem__(self, key, value):
        if key not in self._validator.properties:
            raise KeyError('Invalid key "%s"' % key)
        value = self._validator.properties[key].validate(value)
        dict_type.__setitem__(self, key, value)

    def __getattr__(self, key):
        if key in self._validator.properties:
            return dict_type.__getitem__(self, key)
        return self.__getattribute__(key)

    def __getitem__(self, key):
        value = dict_type.__getitem__(self, key)
        validator = self._validator.properties[key]
        if validator.format in validators.FORMATS:
            formatter = validators.FORMATS[validator.format]
            return formatter.to_string(value)
        return value
