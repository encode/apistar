import collections
import io
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

RequestStream = typing.NewType('RequestStream', io.BufferedIOBase)
RequestData = typing.TypeVar('RequestData')
ResponseData = typing.TypeVar('ResponseData')


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


class ResponseHeaders(Headers):
    def __setitem__(self, key: str, value: str) -> None:
        """
        Add or update a header.
        """
        key_lower = key.lower()
        if key_lower in self._dict:
            # Drop any existing occurances from the list.
            self._list = [
                (item_key, item_value) for item_key, item_value in self._list
                if item_key != key_lower
            ]
        self._dict[key_lower] = value
        self._list.append((key_lower, value))

    def append(self, key: str, value: str) -> None:
        """
        Add a header, preserving any existing occurances.
        """
        key_lower = key.lower()
        if key_lower not in self._dict:
            self._dict[key_lower] = value
        self._list.append((key_lower, value))

    def update(self, other: StringPairs) -> None:
        if hasattr(other, 'items'):
            other = typing.cast(StringPairsMapping, other)
            for key, value in other.items():
                self[key] = value
        else:
            other = typing.cast(StringPairsSequence, other)
            for key, value in other:
                self[key] = value


class Session(object):
    def __init__(self, session_id: str, data: typing.Dict[str, typing.Any]=None) -> None:
        if data is not None:
            self.data = data
            self.is_new = False
        else:
            self.data = {}
            self.is_new = True

        self.is_modified = False
        self.session_id = session_id

    def __getitem__(self, key: str) -> typing.Any:
        return self.data[key]

    def __contains__(self, key: str) -> bool:
        return key in self.data

    def get(self, key: str, default=None) -> typing.Any:
        return self.data.get(key, default)

    def __setitem__(self, key: str, value: typing.Any) -> None:
        self.data[key] = value
        self.is_modified = True

    def __delitem__(self, key: str):
        del self.data[key]
        self.is_modified = True


class Request():
    def __init__(self,
                 method: Method,
                 url: URL,
                 headers: Headers=None,
                 body: Body=None) -> None:
        if headers is None:  # pragma: nocover
            headers = Headers({})
        if body is None:  # pragma: nocover
            body = Body(b'')

        self.method = method
        self.url = url
        self.headers = headers
        self.body = body


class Response(collections.abc.Iterable):
    def __init__(self,
                 content: typing.Any=b'',
                 status: int=200,
                 headers: StringPairs=None,
                 content_type: str=None) -> None:
        self.content = content
        self.status = status
        self.headers = ResponseHeaders(headers) or ResponseHeaders()
        self.content_type = content_type

    def __iter__(self) -> typing.Iterator:
        return iter((self.content, self.status, self.headers, self.content_type))
