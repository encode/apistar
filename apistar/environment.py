import os
from typing import Any, Dict, List, Mapping  # noqa

from apistar import exceptions, schema


class Environment(schema.Object):
    properties = {}  # type: Dict[str, Any]
    _os_environ = os.environ

    def __new__(cls, *args: List) -> Dict:
        return dict.__new__(cls, *args)

    def __init__(self, value: Mapping=None) -> None:
        if value is None:
            value = self._os_environ

        try:
            super().__init__(value)
        except exceptions.SchemaError as exc:
            raise exceptions.ConfigurationError(exc.detail)
