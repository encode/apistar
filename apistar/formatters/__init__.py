from apistar.exceptions import ParseError, ValidationError
from apistar.formatters.json_parser import parse_json
from apistar.formatters.yaml_parser import parse_yaml


class Mark:
    def __init__(self, content, index):
        self.index = index
        lines = content[:index + 1].splitlines()
        self.row = len(lines)
        self.column = len(lines[-1]) if lines else 0


class Error:
    def __init__(self, message, content, start_index, end_index):
        self.message = message
        self.start = Mark(content, start_index)
        self.end = Mark(content, end_index)

    def __repr__(self):
        return '<Error %s at line %d, column %s.>' % (
            repr(self.message),
            self.start.row,
            self.start.column
        )


def get_errors_list(error_detail, prefix=()):
    """
    Given an 'error_detail' from a ValidationError, returns a list of
    two-tuples of (index, message).
    """
    errors = []
    if isinstance(error_detail, str):
        errors.append((prefix, error_detail))
    elif isinstance(error_detail, dict):
        for key, value in error_detail.items():
            errors.extend(get_errors_list(value, prefix + (key,)))
    return errors


def get_errors(content, exc, content_type=None):
    assert content_type in ('json', 'yaml')
    assert isinstance(exc, (ParseError, ValidationError))

    if isinstance(exc, ParseError):
        return [
            Error(exc.short_message, exc.pos, exc.pos)
        ]

    if content_type == 'json':
        nodes = parse_json(content)
    elif content_type == 'yaml':
        nodes = parse_yaml(content)
    errors = []
    for prefix, message in get_errors_list(exc.detail):
        node = nodes.lookup(prefix)
        if message.code in ('invalid_key', 'invalid_property'):
            error = Error(message, content, node.key_start, node.key_end)
        else:
            error = Error(message, content, node.start, node.end)
        errors.append(error)
    return sorted(errors, key=lambda e: e.start.index)
