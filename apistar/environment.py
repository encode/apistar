import os
from typing import Dict, List  # noqa

from apistar import exceptions, schema


class Environment(schema.Object):
    properties = {}  # type: Dict[str, type]
    required = []  # type: List[str]

    def __new__(cls, *args):
        return dict.__new__(cls, *args)

    def __init__(self, value=None):
        if value is None:
            value = os.environ

        try:
            super().__init__(value)
        except exceptions.SchemaError as exc:
            raise exceptions.ConfigurationError(exc.detail)
