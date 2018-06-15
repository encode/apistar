import yaml
from yaml.loader import SafeLoader

from apistar.tokenize.tokens import DictToken, ListToken, ScalarToken


def tokenize_yaml(content):
    class CustomLoader(SafeLoader):
        pass

    def construct_mapping(loader, node):
        start = node.start_mark.index
        end = node.end_mark.index
        mapping = loader.construct_mapping(node)
        return DictToken(mapping, start, end - 1)

    def construct_sequence(loader, node):
        start = node.start_mark.index
        end = node.end_mark.index
        value = loader.construct_sequence(node)
        return ListToken(value, start, end - 1)

    def construct_scalar(loader, node):
        start = node.start_mark.index
        end = node.end_mark.index
        value = loader.construct_scalar(node)
        return ScalarToken(value, start, end - 1)

    def construct_int(loader, node):
        start = node.start_mark.index
        end = node.end_mark.index
        value = loader.construct_yaml_int(node)
        return ScalarToken(value, start, end - 1)

    def construct_float(loader, node):
        start = node.start_mark.index
        end = node.end_mark.index
        value = loader.construct_yaml_float(node)
        return ScalarToken(value, start, end - 1)

    def construct_bool(loader, node):
        start = node.start_mark.index
        end = node.end_mark.index
        value = loader.construct_yaml_bool(node)
        return ScalarToken(value, start, end - 1)

    def construct_null(loader, node):
        start = node.start_mark.index
        end = node.end_mark.index
        value = loader.construct_yaml_null(node)
        return ScalarToken(value, start, end - 1)

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

    return yaml.load(content, CustomLoader)
