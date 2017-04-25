import os
from typing import Dict  # noqa

from apistar import exceptions, schema


class Environment(schema.Object):
    properties = {}  # type: Dict[str, type]

    def __new__(cls, *args):
        if not args:
            args = [os.environ]
        return super().__new__(cls, *args)

    def __init__(self, value):
        try:
            super().__init__(value)
        except exceptions.SchemaError as exc:
            raise exceptions.ConfigurationError(exc.detail)
