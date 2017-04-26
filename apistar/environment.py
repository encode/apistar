import os
from typing import Any, Dict  # noqa

from apistar import exceptions, schema


class Environment(schema.Object):
    properties = {}  # type: Dict[str, Any]
    _os_environ = os.environ

    def __new__(cls, *args):
        return dict.__new__(cls, *args)

    def __init__(self, value=None):
        if value is None:
            value = self._os_environ

        try:
            super().__init__(value)
        except exceptions.SchemaError as exc:
            raise exceptions.ConfigurationError(exc.detail)
