import collections
import typing

Method = typing.NewType('Method', str)
URL = typing.NewType('URL', str)
Scheme = typing.NewType('Scheme', str)
Host = typing.NewType('Host', str)
Port = typing.NewType('Port', int)
Path = typing.NewType('Path', str)
QueryString = typing.NewType('QueryString', str)
QueryParams = typing.NewType('QueryParams', dict)
QueryParam = typing.NewType('QueryParam', str)
# Headers = typing.NewType('Headers', dict)
Header = typing.NewType('Header', str)
Body = typing.NewType('Body', bytes)

RequestData = typing.TypeVar('RequestData')


class Headers(collections.Mapping):
    """An immutable, case-insensitive dictionary."""

    def __init__(self, *args, **kwargs):
        if len(args) == 1 and not kwargs and isinstance(args[0], dict):
            value = args[0]
        else:
            value = dict(*args, **kwargs)
        self._dict = {k.lower(): v for k, v in value.items()}

    def __getitem__(self, key):
        return self._dict[key.lower()]

    def __iter__(self):
        return iter(self._dict)

    def __len__(self):
        return len(self._dict)

    def __repr__(self):
        return 'Headers(%s)' % repr(self._dict)


class Response(collections.abc.Iterable):
    def __init__(self,
                 content: typing.Any,
                 status: int=200,
                 headers: typing.Dict[str, str]=None,
                 content_type: str=None) -> None:
        self.content = content
        self.status = status
        self.headers = headers or {}
        self.content_type = content_type

    def __iter__(self) -> typing.Iterator:
        return iter((self.content, self.status, self.headers, self.content_type))
