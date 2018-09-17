import json

from apistar import types, validators
from apistar.compat import dict_type
from apistar.exceptions import ErrorMessage, ParseError

JSON_SCHEMA = validators.Object(
    def_name='JSONSchema',
    properties=[
        ('$ref', validators.String()),
        ('type', validators.String() | validators.Array(items=validators.String())),
        ('enum', validators.Array(unique_items=True, min_items=1)),
        ('definitions', validators.Object(additional_properties=validators.Ref('JSONSchema'))),

        # String
        ('minLength', validators.Integer(minimum=0)),
        ('maxLength', validators.Integer(minimum=0)),
        ('pattern', validators.String(format='regex')),
        ('format', validators.String()),

        # Numeric
        ('minimum', validators.Number()),
        ('maximum', validators.Number()),
        ('exclusiveMinimum', validators.Boolean()),
        ('exclusiveMaximum', validators.Boolean()),
        ('multipleOf', validators.Number(minimum=0.0, exclusive_minimum=True)),

        # Object
        ('properties', validators.Object(additional_properties=validators.Ref('JSONSchema'))),
        ('minProperties', validators.Integer(minimum=0)),
        ('maxProperties', validators.Integer(minimum=0)),
        ('patternProperties', validators.Object(additional_properties=validators.Ref('JSONSchema'))),
        ('additionalProperties', validators.Ref('JSONSchema') | validators.Boolean()),
        ('required', validators.Array(items=validators.String(), min_items=1, unique_items=True)),

        # Array
        ('items', validators.Ref('JSONSchema') | validators.Array(items=validators.Ref('JSONSchema'), min_items=1)),
        ('additionalItems', validators.Ref('JSONSchema') | validators.Boolean()),
        ('minItems', validators.Integer(minimum=0)),
        ('maxItems', validators.Integer(minimum=0)),
        ('uniqueItems', validators.Boolean()),
    ],
)


def decode(struct):
    typestrings = get_typestrings(struct)
    if is_any(typestrings, struct):
        return validators.Any()

    allow_null = False
    if 'null' in typestrings:
        allow_null = True
        typestrings.remove('null')

    if len(typestrings) == 1:
        return load_type(typestrings.pop(), struct, allow_null)
    else:
        items = [load_type(typename, struct, False) for typename in typestrings]
        return validators.Union(items=items, allow_null=allow_null)


def get_typestrings(struct):
    """
    Return the valid schema types as a set.
    """
    type_strings = struct.get('type', [])
    if isinstance(type_strings, str):
        type_strings = {type_strings}
    else:
        type_strings = set(type_strings)

    if not type_strings:
        type_strings = {
            'null', 'boolean', 'object',
            'array', 'number', 'string'
        }

    if 'integer' in type_strings and 'number' in type_strings:
        type_strings.remove('integer')

    return type_strings


def is_any(type_strings, struct):
    """
    Return true if all types are valid, and there are no type constraints.
    """
    ALL_PROPERTY_NAMES = {
        'exclusiveMaximum', 'format', 'minItems', 'pattern', 'required', 'multipleOf', 'maximum',
        'minimum', 'maxItems', 'minLength', 'uniqueItems', 'additionalItems', 'maxLength', 'items',
        'exclusiveMinimum', 'properties', 'additionalProperties', 'minProperties', 'maxProperties',
        'patternProperties'
    }

    return len(type_strings) == 6 and not set(struct.keys()) & ALL_PROPERTY_NAMES


def load_type(typename, struct, allow_null):
    attrs = {'allow_null': True} if allow_null else {}

    if typename == 'string':
        if 'minLength' in struct:
            attrs['min_length'] = struct['minLength']
        if 'maxLength' in struct:
            attrs['max_length'] = struct['maxLength']
        if 'pattern' in struct:
            attrs['pattern'] = struct['pattern']
        if 'format' in struct:
            attrs['format'] = struct['format']
        return validators.String(**attrs)

    if typename in ['number', 'integer']:
        if 'minimum' in struct:
            attrs['minimum'] = struct['minimum']
        if 'maximum' in struct:
            attrs['maximum'] = struct['maximum']
        if 'exclusiveMinimum' in struct:
            attrs['exclusive_minimum'] = struct['exclusiveMinimum']
        if 'exclusiveMaximum' in struct:
            attrs['exclusive_maximum'] = struct['exclusiveMaximum']
        if 'multipleOf' in struct:
            attrs['multiple_of'] = struct['multipleOf']
        if 'format' in struct:
            attrs['format'] = struct['format']
        if typename == 'integer':
            return validators.Integer(**attrs)
        return validators.Number(**attrs)

    if typename == 'boolean':
        return validators.Boolean(**attrs)

    if typename == 'object':
        if 'properties' in struct:
            attrs['properties'] = dict_type([
                (key, decode(value))
                for key, value in struct['properties'].items()
            ])
        if 'required' in struct:
            attrs['required'] = struct['required']
        if 'minProperties' in struct:
            attrs['min_properties'] = struct['minProperties']
        if 'maxProperties' in struct:
            attrs['max_properties'] = struct['maxProperties']
        if 'required' in struct:
            attrs['required'] = struct['required']
        if 'patternProperties' in struct:
            attrs['pattern_properties'] = dict_type([
                (key, decode(value))
                for key, value in struct['patternProperties'].items()
            ])
        if 'additionalProperties' in struct:
            if isinstance(struct['additionalProperties'], bool):
                attrs['additional_properties'] = struct['additionalProperties']
            else:
                attrs['additional_properties'] = decode(struct['additionalProperties'])
        return validators.Object(**attrs)

    if typename == 'array':
        if 'items' in struct:
            if isinstance(struct['items'], list):
                attrs['items'] = [decode(item) for item in struct['items']]
            else:
                attrs['items'] = decode(struct['items'])
        if 'additionalItems' in struct:
            if isinstance(struct['additionalItems'], bool):
                attrs['additional_items'] = struct['additionalItems']
            else:
                attrs['additional_items'] = decode(struct['additionalItems'])
        if 'minItems' in struct:
            attrs['min_items'] = struct['minItems']
        if 'maxItems' in struct:
            attrs['max_items'] = struct['maxItems']
        if 'uniqueItems' in struct:
            attrs['unique_items'] = struct['uniqueItems']
        return validators.Array(**attrs)

    assert False


class JSONSchema:
    def decode(self, bytestring, **options):
        try:
            data = json.loads(
                bytestring.decode('utf-8'),
                object_pairs_hook=dict_type
            )
        except ValueError as exc:
            message = ErrorMessage(text='Malformed JSON. %s' % exc, code='parse_failed')
            raise ParseError(messages=[message]) from None
        jsonschema = JSON_SCHEMA.validate(data)
        return decode(jsonschema)

    def decode_from_data_structure(self, struct):
        jsonschema = JSON_SCHEMA.validate(struct)
        return decode(jsonschema)

    def encode(self, item, **options):
        defs = dict_type()
        struct = self.encode_to_data_structure(item, defs=defs, def_prefix='#/definitions/')
        struct['definitions'] = defs
        if options.get('to_data_structure'):
            return struct

        indent = options.get('indent')
        if indent:
            kwargs = {
                'ensure_ascii': False,
                'indent': 4,
                'separators': (',', ': ')
            }
        else:
            kwargs = {
                'ensure_ascii': False,
                'indent': None,
                'separators': (',', ':')
            }
        return json.dumps(struct, **kwargs).encode('utf-8')

    def encode_to_data_structure(self, item, defs=None, def_prefix=None, is_def=False):
        if issubclass(item, types.Type):
            item = item.validator

        if defs is not None and item.def_name and not is_def:
            defs[item.def_name] = self.encode_to_data_structure(
                item, defs, def_prefix, is_def=True
            )
            return {'$ref': def_prefix + item.def_name}

        value = dict_type()
        if item.title:
            value['title'] = item.title
        if item.description:
            value['description'] = item.description
        if item.has_default():
            value['default'] = item.default
        if getattr(item, 'allow_null') is True:
            value['nullable'] = True

        if isinstance(item, validators.String):
            value['type'] = 'string'
            if item.max_length is not None:
                value['maxLength'] = item.max_length
            if item.min_length is not None:
                value['minLength'] = item.min_length
            if item.pattern is not None:
                value['pattern'] = item.pattern
            if item.format is not None:
                value['format'] = item.format
            return value

        elif isinstance(item, validators.NumericType):
            if isinstance(item, validators.Integer):
                value['type'] = 'integer'
            else:
                value['type'] = 'number'

            if item.minimum is not None:
                value['minimum'] = item.minimum
            if item.maximum is not None:
                value['maximum'] = item.maximum
            if item.exclusive_minimum:
                value['exclusiveMinimum'] = item.exclusive_minimum
            if item.exclusive_maximum:
                value['exclusiveMaximum'] = item.exclusive_maximum
            if item.multiple_of is not None:
                value['multipleOf'] = item.multiple_of
            if item.format is not None:
                value['format'] = item.format
            return value

        elif isinstance(item, validators.Boolean):
            value['type'] = 'boolean'
            return value

        elif isinstance(item, validators.Object):
            value['type'] = 'object'
            if item.properties:
                value['properties'] = dict_type([
                    (key, self.encode_to_data_structure(value, defs, def_prefix))
                    for key, value in item.properties.items()
                ])
            if item.required:
                value['required'] = item.required
            return value

        elif isinstance(item, validators.Array):
            value['type'] = 'array'
            if item.items is not None:
                value['items'] = self.encode_to_data_structure(item.items, defs, def_prefix)
            if item.additional_items:
                value['additionalItems'] = item.additional_items
            if item.min_items is not None:
                value['minItems'] = item.min_items
            if item.max_items is not None:
                value['maxItems'] = item.max_items
            if item.unique_items:
                value['uniqueItems'] = item.unique_items
            return value

        raise Exception('Cannot encode item %s' % item)
