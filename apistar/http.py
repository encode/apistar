import collections
import typing

Method = typing.NewType('Method', str)
URL = typing.NewType('URL', str)
Scheme = typing.NewType('Scheme', str)
Host = typing.NewType('Host', str)
Port = typing.NewType('Port', int)
Path = typing.NewType('Path', str)
QueryString = typing.NewType('QueryString', str)
QueryParam = typing.NewType('QueryParam', str)
Header = typing.NewType('Header', str)
Body = typing.NewType('Body', bytes)

RequestData = typing.TypeVar('RequestData')


class QueryParams(collections.Mapping):
    """
    An immutable multidict.
    """

    def __init__(self, value):
        if hasattr(value, 'items'):
            items = list(value.items())
        else:
            items = list(value)
        self._dict = {k: v for k, v in reversed(items)}
        self._list = items

    def get_list(self, key):
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


class Headers(collections.Mapping):
    """
    An immutable, case-insensitive multidict.
    """

    def __init__(self, value):
        if hasattr(value, 'items'):
            items = [(k.lower(), v) for k, v in list(value.items())]
        else:
            items = [(k.lower(), v) for k, v in list(value)]
        self._dict = {k: v for k, v in reversed(items)}
        self._list = items

    def get_list(self, key):
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

    def __getitem__(self, key):
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
