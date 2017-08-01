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


class Response(object):
    def __init__(self,
                 content: typing.Any,
                 status: int=200,
                 headers: typing.Dict[str, str]=None) -> None:
        self.content = content
        self.status = status
        self.headers = headers or {}

    def __iter__(self):
        return iter((self.content, self.status, self.headers))
