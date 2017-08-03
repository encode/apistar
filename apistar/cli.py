import collections
import typing


class Command(collections.abc.Iterable):
    def __init__(self,
                 name: str,
                 handler: typing.Callable) -> None:
        self.name = name
        self.handler = handler

    def __iter__(self) -> typing.Iterator:
        return iter((self.name, self.handler))
