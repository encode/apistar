import os

import jinja2

from apistar.exceptions import ValidationError
from apistar.schemas.config import APISTAR_CONFIG
from apistar.schemas.jsonschema import JSON_SCHEMA
from apistar.schemas.openapi import OPEN_API, OpenAPI
from apistar.schemas.swagger import SWAGGER, Swagger
from apistar.tokenize.tokenize_json import tokenize_json
from apistar.tokenize.tokenize_yaml import tokenize_yaml

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
                'config': 'Invalid configuration file.',
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


def docs(content, format, base_format=None, theme='apistar', schema_url=None, static_url='/static/'):
    value = validate(content, format, base_format=base_format)

    decoder = {
        'openapi': OpenAPI,
        'swagger': Swagger
    }[format]
    document = decoder().load(value)

    loader = jinja2.PrefixLoader({
        theme: jinja2.PackageLoader('apistar', os.path.join('themes', theme, 'templates'))
    })
    env = jinja2.Environment(autoescape=True, loader=loader)

    if isinstance(static_url, str):
        def static_url_func(path):
            return static_url.rstrip('/') + '/' + path.lstrip('/')
    else:
        static_url_func = static_url

    template = env.get_template(os.path.join(theme, 'index.html'))
    return template.render(
        document=document,
        langs=['javascript', 'python'],
        code_style=None,
        static_url=static_url_func,
        schema_url=schema_url
    )
