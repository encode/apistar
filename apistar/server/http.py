import typing
from urllib.parse import urlparse

Method = typing.NewType('Method', str)
Scheme = typing.NewType('Scheme', str)
Host = typing.NewType('Host', str)
Port = typing.NewType('Port', int)
Path = typing.NewType('Path', str)
QueryString = typing.NewType('QueryString', str)
QueryParam = typing.NewType('QueryParam', str)
Header = typing.NewType('Header', str)
Body = typing.NewType('Body', bytes)
PathParams = typing.NewType('PathParams', dict)
PathParam = typing.NewType('PathParam', str)


class URL(str):
    """
    A string that also supports accessing the parsed URL components.
    eg. `url.components.query`
    """

    @property
    def components(self):
        if not hasattr(self, '_components'):
            self._components = urlparse(self)
        return self._components


# Type annotations for valid `__init__` values to QueryParams and Headers.
StringPairsSequence = typing.Sequence[typing.Tuple[str, str]]
StringPairsMapping = typing.Mapping[str, str]
StringPairs = typing.Union[StringPairsSequence, StringPairsMapping]


class QueryParams(typing.Mapping[str, str]):
    """
    An immutable multidict.
    """

    def __init__(self, value: StringPairs) -> None:
        if hasattr(value, 'items'):
            value = typing.cast(StringPairsMapping, value)
            items = list(value.items())
        else:
            value = typing.cast(StringPairsSequence, value)
            items = list(value)
        self._dict = {k: v for k, v in reversed(items)}
        self._list = items

    def get_list(self, key: str) -> typing.List[str]:
        return [
            item_value for item_key, item_value in self._list
            if item_key == key
        ]

    def keys(self):
        return [key for key, value in self._list]

    def values(self):
        return [value for key, value in self._list]

    def items(self):
        return list(self._list)

    def get(self, key, default=None):
        if key in self._dict:
            return self._dict[key]
        else:
            return default

    def __getitem__(self, key):
        return self._dict[key]

    def __contains__(self, key):
        return key in self._dict

    def __iter__(self):
        return iter(self._list)

    def __len__(self):
        return len(self._list)

    def __eq__(self, other):
        if not isinstance(other, QueryParams):
            other = QueryParams(other)
        return sorted(self._list) == sorted(other._list)

    def __repr__(self):
        return 'QueryParams(%s)' % repr(self._list)


class Headers(typing.Mapping[str, str]):
    """
    An immutable, case-insensitive multidict.
    """

    def __init__(self, value: StringPairs=None) -> None:
        if value is None:
            value = []
        if hasattr(value, 'items'):
            value = typing.cast(StringPairsMapping, value)
            items = [(k.lower(), v) for k, v in list(value.items())]
        else:
            value = typing.cast(StringPairsSequence, value)
            items = [(k.lower(), v) for k, v in list(value)]
        self._dict = {k: v for k, v in reversed(items)}
        self._list = items

    def get_list(self, key: str) -> typing.List[str]:
        key_lower = key.lower()
        return [
            item_value for item_key, item_value in self._list
            if item_key == key_lower
        ]

    def keys(self):
        return [key for key, value in self._list]

    def values(self):
        return [value for key, value in self._list]

    def items(self):
        return list(self._list)

    def get(self, key, default=None):
        if key in self._dict:
            return self._dict[key]
        else:
            return default

    def __getitem__(self, key: str):
        return self._dict[key.lower()]

    def __contains__(self, key):
        return key.lower() in self._dict

    def __iter__(self):
        return iter(self._list)

    def __len__(self):
        return len(self._list)

    def __eq__(self, other):
        if not isinstance(other, Headers):
            other = Headers(other)
        return sorted(self._list) == sorted(other._list)

    def __repr__(self):
        return 'Headers(%s)' % repr(self._list)


class Request():
    def __init__(self,
                 method: Method,
                 url: URL,
                 headers: Headers=None,
                 body: Body=None) -> None:
        self.method = method
        self.url = url
        self.headers = Headers() if (headers is None) else headers
        self.body = Body(b'') if (body is None) else body


class Response():
    def __init__(self,
                 content: typing.Any=b'',
                 status: int=200,
                 headers: StringPairs=None,
                 content_type: str=None) -> None:
        self.content = content
        self.status = status
        self.headers = Headers() if (headers is None) else Headers(headers)
        self.content_type = content_type
