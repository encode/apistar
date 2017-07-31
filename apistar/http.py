import typing


Method = typing.NewType('Method', str)
URL = typing.NewType('URL', str)
Scheme = typing.NewType('Scheme', str)
Host = typing.NewType('Host', str)
Port = typing.NewType('Port', int)
Path = typing.NewType('Path', str)
QueryString = typing.NewType('QueryString', str)
QueryParams = typing.NewType('QueryParams', typing.Dict[str, str])
QueryParam = typing.NewType('QueryParam', str)
Headers = typing.NewType('Headers', typing.Dict[str, str])
Header = typing.NewType('Header', str)
Body = typing.NewType('Body', bytes)

RequestData = typing.TypeVar('RequestData')

Response = typing.NamedTuple('Response', [
    ('data', typing.Any),
    ('status', int),
    ('headers', typing.Dict[str, str])
])
Response.__new__.__defaults__ = (None, 200, {})
