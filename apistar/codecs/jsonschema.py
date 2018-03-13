import json

from apistar import types
from apistar.codecs.base import BaseCodec
from apistar.compat import dict_type
from apistar.exceptions import ParseError

JSON_SCHEMA = types.Object(
    self_ref='JSONSchema',
    properties=[
        ('$ref', types.String()),
        ('type', types.String() | types.Array(items=types.String())),
        ('enum', types.Array(unique_items=True, min_items=1)),
        ('definitions', types.Object(additional_properties=types.Ref('JSONSchema'))),

        # String
        ('minLength', types.Integer(minimum=0, default=0)),
        ('maxLength', types.Integer(minimum=0)),
        ('pattern', types.String(format='regex')),
        ('format', types.String()),

        # Numeric
        ('minimum', types.Number()),
        ('maximum', types.Number()),
        ('exclusiveMinimum', types.Boolean(default=False)),
        ('exclusiveMaximum', types.Boolean(default=False)),
        ('multipleOf', types.Number(minimum=0.0, exclusive_minimum=True)),

        # Object
        ('properties', types.Object(additional_properties=types.Ref('JSONSchema'))),
        ('minProperties', types.Integer(minimum=0, default=0)),
        ('maxProperties', types.Integer(minimum=0)),
        ('patternProperties', types.Object(additional_properties=types.Ref('JSONSchema'))),
        ('additionalProperties', types.Ref('JSONSchema') | types.Boolean()),
        ('required', types.Array(items=types.String(), min_items=1, unique_items=True)),

        # Array
        ('items', types.Ref('JSONSchema') | types.Array(items=types.Ref('JSONSchema'), min_items=1)),
        ('additionalItems', types.Ref('JSONSchema') | types.Boolean()),
        ('minItems', types.Integer(minimum=0, default=9)),
        ('maxItems', types.Integer(minimum=0)),
        ('uniqueItems', types.Boolean()),
    ]
)


def decode(struct):
    typestrings = get_typestrings(struct)
    if is_any(typestrings, struct):
        return types.Any()

    allow_null = False
    if 'null' in typestrings:
        allow_null = True
        typestrings.remove('null')

    if len(typestrings) == 1:
        return load_type(typestrings.pop(), struct, allow_null)
    else:
        items = [load_type(typename, struct, False) for typename in typestrings]
        return types.Union(items=items, allow_null=allow_null)


def get_typestrings(struct):
    """
    Return the valid schema types as a set.
    """
    type_strings = struct.get('type', [])
    if isinstance(type_strings, str):
        type_strings = set([type_strings])
    else:
        type_strings = set(type_strings)

    if not type_strings:
        type_strings = set(['null', 'boolean', 'object', 'array', 'number', 'string'])

    if 'integer' in type_strings and 'number' in type_strings:
        type_strings.remove('integer')

    return type_strings


def is_any(type_strings, struct):
    """
    Return true if all types are valid, and there are no type constraints.
    """
    ALL_PROPERTY_NAMES = set([
        'exclusiveMaximum', 'format', 'minItems', 'pattern', 'required',
        'multipleOf', 'maximum', 'minimum', 'maxItems', 'minLength',
        'uniqueItems', 'additionalItems', 'maxLength', 'items',
        'exclusiveMinimum', 'properties', 'additionalProperties',
        'minProperties', 'maxProperties', 'patternProperties'
    ])
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
        return types.String(**attrs)

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
            return types.Integer(**attrs)
        return types.Number(**attrs)

    if typename == 'boolean':
        return types.Boolean(**attrs)

    if typename == 'object':
        if 'properties' in struct:
            attrs['properties'] = {
                key: decode(value)
                for key, value in struct['properties'].items()
            }
        if 'required' in struct:
            attrs['required'] = struct['required']
        if 'minProperties' in struct:
            attrs['min_properties'] = struct['minProperties']
        if 'maxProperties' in struct:
            attrs['max_properties'] = struct['maxProperties']
        if 'required' in struct:
            attrs['required'] = struct['required']
        if 'patternProperties' in struct:
            attrs['pattern_properties'] = {
                key: decode(value)
                for key, value in struct['patternProperties'].items()
            }
        if 'additionalProperties' in struct:
            if isinstance(struct['additionalProperties'], bool):
                attrs['additional_properties'] = struct['additionalProperties']
            else:
                attrs['additional_properties'] = decode(struct['additionalProperties'])
        return types.Object(**attrs)

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
        return types.Array(**attrs)

    assert False


class JSONSchemaCodec(BaseCodec):
    media_type = 'application/schema+json'
    format = 'jsonschema'

    def decode(self, bytestring, **options):
        try:
            data = json.loads(
                bytestring.decode('utf-8'),
                object_pairs_hook=dict_type
            )
        except ValueError as exc:
            raise ParseError('Malformed JSON. %s' % exc)
        jsonschema = JSON_SCHEMA.validate(data)
        return decode(jsonschema)

    def decode_from_data_structure(self, struct):
        jsonschema = JSON_SCHEMA.validate(struct)
        return decode(jsonschema)

    def encode(self, item, **options):
        struct = self.encode_to_data_structure(item)
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

    def encode_to_data_structure(self, item):
        if isinstance(item, types.String):
            value = {'type': 'string'}
            if item.max_length is not None:
                value['maxLength'] = item.max_length
            if item.min_length is not None:
                value['minLength'] = item.min_length
            if item.pattern is not None:
                value['pattern'] = item.pattern
            if item.format is not None:
                value['format'] = item.format
            return value

        if isinstance(item, types.NumericType):
            if isinstance(item, types.Integer):
                value = {'type': 'integer'}
            else:
                value = {'type': 'number'}

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

        if isinstance(item, types.Boolean):
            return {'type': 'boolean'}

        if isinstance(item, types.Object):
            value = {'type': 'object'}
            if item.properties:
                value['properties'] = {
                    key: self.encode_to_data_structure(value)
                    for key, value in item.properties.items()
                }
            if item.required:
                value['required'] = item.required
            return value

        if isinstance(item, types.Array):
            value = {'type': 'array'}
            if item.items is not None:
                value['items'] = self.encode_to_data_structure(item.items)
            if item.additional_items:
                value['additionalItems'] = item.additional_items
            if item.min_items is not None:
                value['minItems'] = item.min_items
            if item.max_items is not None:
                value['maxItems'] = item.max_items
            if item.unique_items is not None:
                value['uniqueItems'] = item.unique_items
            return value

        raise Exception('Cannot encode item %s' % item)
