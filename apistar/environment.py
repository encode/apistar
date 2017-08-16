import os
import typing

from apistar import exceptions, typesystem


class Environment(typesystem.Object):
    properties = {}  # type: typing.Dict[str, typing.Any]
    _os_environ = os.environ

    def __init__(self, value: typing.Mapping=None) -> None:
        if value is None:
            value = self._os_environ

        try:
            super().__init__(value)
        except exceptions.TypeSystemError as exc:
            raise exceptions.ConfigurationError(exc.detail) from None
