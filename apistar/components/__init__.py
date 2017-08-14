import collections
import typing


class Component(collections.abc.Iterable):
    def __init__(self,
                 cls: type,
                 init: typing.Callable=None,
                 preload: bool=True) -> None:
        self.cls = cls
        if init is not None:
            self.init = init
        else:
            self.init = cls  # type: ignore
        self.preload = preload

    def __iter__(self) -> typing.Iterator:
        return iter((self.cls, self.init, self.preload))
