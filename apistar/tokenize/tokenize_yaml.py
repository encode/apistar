import yaml
from yaml.loader import SafeLoader

from apistar.exceptions import ErrorMessage, ParseError, Position
from apistar.tokenize.tokens import DictToken, ListToken, ScalarToken


def _get_position(content, index):
    return Position(
        line_no=content.count('\n', 0, index) + 1,
        column_no=index - content.rfind('\n', 0, index),
        index=index
    )


def tokenize_yaml(content):
    class CustomLoader(SafeLoader):
        pass

    def construct_mapping(loader, node):
        start = node.start_mark.index
        end = node.end_mark.index
        mapping = loader.construct_mapping(node)
        return DictToken(mapping, start, end - 1, content=content)

    def construct_sequence(loader, node):
        start = node.start_mark.index
        end = node.end_mark.index
        value = loader.construct_sequence(node)
        return ListToken(value, start, end - 1, content=content)

    def construct_scalar(loader, node):
        start = node.start_mark.index
        end = node.end_mark.index
        value = loader.construct_scalar(node)
        return ScalarToken(value, start, end - 1, content=content)

    def construct_int(loader, node):
        start = node.start_mark.index
        end = node.end_mark.index
        value = loader.construct_yaml_int(node)
        return ScalarToken(value, start, end - 1, content=content)

    def construct_float(loader, node):
        start = node.start_mark.index
        end = node.end_mark.index
        value = loader.construct_yaml_float(node)
        return ScalarToken(value, start, end - 1, content=content)

    def construct_bool(loader, node):
        start = node.start_mark.index
        end = node.end_mark.index
        value = loader.construct_yaml_bool(node)
        return ScalarToken(value, start, end - 1, content=content)

    def construct_null(loader, node):
        start = node.start_mark.index
        end = node.end_mark.index
        value = loader.construct_yaml_null(node)
        return ScalarToken(value, start, end - 1, content=content)

    CustomLoader.add_constructor(
        yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG,
        construct_mapping)

    CustomLoader.add_constructor(
        yaml.resolver.BaseResolver.DEFAULT_SEQUENCE_TAG,
        construct_sequence)

    CustomLoader.add_constructor(
        yaml.resolver.BaseResolver.DEFAULT_SCALAR_TAG,
        construct_scalar)

    CustomLoader.add_constructor(
        'tag:yaml.org,2002:int',
        construct_int)

    CustomLoader.add_constructor(
        'tag:yaml.org,2002:float',
        construct_float)

    CustomLoader.add_constructor(
        'tag:yaml.org,2002:bool',
        construct_bool)

    CustomLoader.add_constructor(
        'tag:yaml.org,2002:null',
        construct_null)

    assert isinstance(content, (str, bytes))

    if isinstance(content, bytes):
        content = content.decode('utf-8', 'ignore')

    if not content.strip():
        message = ErrorMessage(
            text='No content.',
            code='parse_error',
            position=Position(line_no=1, column_no=1, index=0)
        )
        raise ParseError(errors=[message], summary='Invalid YAML.')

    try:
        return yaml.load(content, CustomLoader)
    except (yaml.scanner.ScannerError, yaml.parser.ParserError) as exc:
        index = getattr(exc, 'index', 0)
        message = ErrorMessage(
            text=exc.problem + ".",
            code='parse_error',
            position=_get_position(content, index=index)
        )
        raise ParseError(messages=[message], summary='Invalid YAML.') from None
