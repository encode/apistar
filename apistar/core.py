import os

import jinja2

from apistar.exceptions import ErrorMessage, ValidationError
from apistar.schemas.config import APISTAR_CONFIG
from apistar.schemas.jsonschema import JSON_SCHEMA
from apistar.schemas.openapi import OPEN_API, OpenAPI
from apistar.schemas.swagger import SWAGGER, Swagger
from apistar.tokenize.tokenize_json import tokenize_json
from apistar.tokenize.tokenize_yaml import tokenize_yaml

__all__ = ['docs', 'parse', 'validate']


FORMAT_CHOICES = ['config', 'jsonschema', 'openapi', 'swagger', None]


def parse(content, encoding, validator=None):
    if encoding not in ("json", "yaml"):
        raise ValueError('encoding must be either "json" or "yaml"')

    if encoding == "json":
        token = tokenize_json(content)
    else:
        token = tokenize_yaml(content)

    value = token.get_value()

    if validator is not None:
        try:
            value = validator.validate(value)
        except ValidationError as exc:
            for message in exc.messages:
                if message.code == 'required':
                    message.position = token.lookup_position(message.index[:-1])
                elif message.code in ['invalid_property', 'invalid_key']:
                    message.position = token.lookup_key_position(message.index)
                else:
                    message.position = token.lookup_position(message.index)
            exc.messages = sorted(exc.messages, key=lambda x: x.position.index)
            raise exc

    return (value, token)


def validate(schema, format=None, encoding=None):
    if format not in FORMAT_CHOICES:
        raise ValueError('format must be one of %s' % FORMAT_CHOICES)

    if isinstance(schema, (str, bytes)):
        if encoding is None:
            raise ValueError('encoding=["json"|"yaml"] is required when passing schema as a string/bytestring.')
        value, token = parse(schema, encoding)
    elif isinstance(schema, dict):
        if encoding is not None:
            raise ValueError('encoding must be `None`.')
        value, token = schema, None
    else:
        raise ValueError('schema must either be a dict, or a string/bytestring.')

    if format is None:
        if isinstance(value, dict) and "openapi" in value and "swagger" not in value:
            format = "openapi"
        elif isinstance(value, dict) and "swagger" in value and "openapi" not in value:
            format = "swagger"
        else:
            message = ErrorMessage(
                text="Unable to determine schema format. Use the 'format' argument.",
                code='unknown_format'
            )
            raise ValidationError(messages=[message])

    validator = {
        'config': APISTAR_CONFIG,
        'jsonschema': JSON_SCHEMA,
        'openapi': OPEN_API,
        'swagger': SWAGGER
    }[format]

    if validator is not None:
        try:
            value = validator.validate(value)
        except ValidationError as exc:
            exc.summary = {
                'config': 'Invalid configuration file.',
                'jsonschema': 'Invalid JSONSchema document.',
                'openapi': 'Invalid OpenAPI schema.',
                'swagger': 'Invalid Swagger schema.',
            }[format]
            if token is not None:
                for message in exc.messages:
                    if message.code == 'required':
                        message.position = token.lookup_position(message.index[:-1])
                    elif message.code in ['invalid_property', 'invalid_key']:
                        message.position = token.lookup_key_position(message.index)
                    else:
                        message.position = token.lookup_position(message.index)
                exc.messages = sorted(exc.messages, key=lambda x: x.position.index)
            raise exc

    if format in ['openapi', 'swagger']:
        decoder = {
            'openapi': OpenAPI,
            'swagger': Swagger
        }[format]
        value = decoder().load(value)

    return value


def docs(schema, format=None, encoding=None, theme='apistar', schema_url=None, static_url=None):
    if format not in [None, 'openapi', 'swagger']:
        raise ValueError('format must be either "openapi" or "swagger"')

    document = validate(schema, format=format, encoding=encoding)

    loader = jinja2.PrefixLoader({
        theme: jinja2.PackageLoader('apistar', os.path.join('themes', theme, 'templates'))
    })
    env = jinja2.Environment(autoescape=True, loader=loader)

    if static_url is None:
        def static_url_func(path):
            return '/' + path.lstrip('/')
    elif isinstance(static_url, str):
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
