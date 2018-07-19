import json

import yaml

from apistar.exceptions import Marker, ParseError, ValidationError
from apistar.tokenize import tokenize_json, tokenize_yaml


def infer_json_or_yaml(content):
    assert isinstance(content, (str, bytes))

    if isinstance(content, bytes):
        content = content.decode('utf-8', 'ignore')

    content = content.strip()
    if not content:
        marker = Marker(0, '')
        raise ParseError('No content.', marker=marker)

    return 'json' if content[0] in '{[' else 'yaml'


def parse_json(content, validator=None):
    assert isinstance(content, (str, bytes))

    if isinstance(content, bytes):
        content = content.decode('utf-8', 'ignore')

    if not content.strip():
        marker = Marker(0, '')
        raise ParseError('No content.', marker=marker, base_format='json')

    try:
        token = None if validator is None else tokenize_json(content)
        data = json.loads(content)
    except json.decoder.JSONDecodeError as exc:
        message = exc.msg + '.'
        marker = Marker(exc.pos, content)
        raise ParseError(message, marker=marker, base_format='json') from None

    if validator is None:
        return data

    try:
        return validator.validate(data)
    except ValidationError as exc:
        exc.set_error_context(token, content)
        raise exc


def parse_yaml(content, validator=None):
    assert isinstance(content, (str, bytes))

    if isinstance(content, bytes):
        content = content.decode('utf-8', 'ignore')

    if not content.strip():
        marker = Marker(0, '')
        raise ParseError('No content.', marker=marker, base_format='yaml')

    try:
        token = None if validator is None else tokenize_yaml(content)
        data = yaml.safe_load(content)
    except (yaml.scanner.ScannerError, yaml.parser.ParserError) as exc:
        position = getattr(exc, 'index', 0)
        marker = Marker(position, content)
        message = exc.problem
        raise ParseError(message, marker=marker, base_format='yaml') from None

    if validator is None:
        return data

    try:
        return validator.validate(data)
    except ValidationError as exc:
        exc.set_error_context(token, content)
        raise exc
