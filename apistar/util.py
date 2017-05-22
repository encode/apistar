import importlib


def resolve_class(cls_or_str):
    """
    Dynamically resolve string type annotations.
    This allows "forward references" to help break circular references.
    """
    if not isinstance(cls_or_str, str):
        return cls_or_str

    path = cls_or_str.split('.')
    package = '.'.join(path[:-1])
    module = path[-1]
    return getattr(importlib.import_module(package), module)
