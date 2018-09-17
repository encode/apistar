from apistar.exceptions import ValidationError
from apistar.schemas.config import APISTAR_CONFIG
from apistar.schemas.jsonschema import JSON_SCHEMA
from apistar.schemas.openapi import OPEN_API
from apistar.schemas.swagger import SWAGGER
from apistar.validate.tokenize_json import tokenize_json
from apistar.validate.tokenize_yaml import tokenize_yaml

__all__ = ['validate']


FORMAT_CHOICES = ['json', 'yaml', 'config', 'jsonschema', 'openapi', 'swagger']


def validate(content, format, base_format=None, schema=None):
    if format not in FORMAT_CHOICES:
        raise ValueError('format must be one of %s' % FORMAT_CHOICES)
    if base_format not in (None, "json", "yaml"):
        raise ValueError('base_format must be either "json", "yaml", or None')

    if base_format is None:
        base_format = {
            'json': 'json',
            'yaml': 'yaml',
            'config': 'yaml',
            'jsonschema': 'json',
            'openapi': 'yaml',
            'swagger': 'yaml'
        }[format]
    if schema is None:
        schema = {
            'json': None,
            'yaml': None,
            'config': APISTAR_CONFIG,
            'jsonschema': JSON_SCHEMA,
            'openapi': OPEN_API,
            'swagger': SWAGGER
        }[format]

    if format == "json" or base_format == "json":
        token = tokenize_json(content)
    else:
        token = tokenize_yaml(content)

    value = token.get_value()

    if schema is not None:
        try:
            value = schema.validate(value)
        except ValidationError as exc:
            exc.summary = {
                'json': 'Does not validate against schema.',
                'yaml': 'Does not validate against schema.',
                'config': 'Invalid APIStar config.',
                'jsonschema': 'Invalid JSONSchema document.',
                'openapi': 'Invalid OpenAPI schema.',
                'swagger': 'Invalid Swagger schema.',
            }[format]
            for message in exc.messages:
                if message.code == 'required':
                    message.position = token.lookup_position(message.index[:-1])
                elif message.code in ['invalid_property', 'invalid_key']:
                    message.position = token.lookup_key_position(message.index)
                else:
                    message.position = token.lookup_position(message.index)
            exc.messages = sorted(exc.messages, key=lambda x: x.position.index)
            raise exc
    return value
