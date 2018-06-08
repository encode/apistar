import json
import typing
from urllib.parse import urlparse

from apistar import types

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
RequestData = typing.TypeVar('RequestData')


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
StrPairs = typing.Sequence[typing.Tuple[str, str]]
StrMapping = typing.Mapping[str, str]


class QueryParams(typing.Mapping[str, str]):
    """
    An immutable multidict.
    """

    def __init__(self, value: typing.Union[StrMapping, StrPairs]=None) -> None:
        if value is None:
            value = []
        if hasattr(value, 'items'):
            items = list(value.items())
        else:
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

    def __init__(self, value: typing.Union[StrMapping, StrPairs]=None) -> None:
        if value is None:
            value = []
        if hasattr(value, 'items'):
            items = [(k.lower(), str(v)) for k, v in list(value.items())]
        else:
            items = [(k.lower(), str(v)) for k, v in list(value)]
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

    def get(self, key: str, default: str=None):
        key = key.lower()
        if key in self._dict:
            return self._dict[key]
        else:
            return default

    def __getitem__(self, key: str):
        return self._dict[key.lower()]

    def __contains__(self, key: str):
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
        return '%s(%s)' % (self.__class__.__name__, repr(self._list))


class MutableHeaders(Headers):
    def __setitem__(self, key: str, value: str):
        key = key.lower()
        value = str(value)

        if key not in self._dict:
            self._dict[key] = value
            self._list.append((key, value))
        else:
            self._dict[key] = value
            self._list = [
                (item_key, value) if item_key == key else (item_key, item_value)
                for item_key, item_value in self._list
            ]


class Request:
    def __init__(self,
                 method: Method,
                 url: URL,
                 headers: Headers=None,
                 body: Body=None) -> None:
        self.method = method
        self.url = url
        self.headers = Headers() if (headers is None) else headers
        self.body = Body(b'') if (body is None) else body


class Response:
    media_type = None
    charset = 'utf-8'

    def __init__(self,
                 content: typing.Any,
                 status_code: int=200,
                 headers: typing.Union[StrMapping, StrPairs]=None,
                 exc_info=None) -> None:
        self.content = self.render(content)
        self.status_code = status_code
        self.headers = MutableHeaders(headers)
        self.set_default_headers()
        self.exc_info = exc_info

    def render(self, content: typing.Any) -> bytes:
        if isinstance(content, bytes):
            return content
        elif isinstance(content, str) and self.charset is not None:
            return content.encode(self.charset)

        valid_types = "bytes" if self.charset is None else "string or bytes"
        raise RuntimeError(
            "%s content must be %s. Got %s." %
            (self.__class__.__name__, valid_types, type(content).__name__)
        )

    def set_default_headers(self):
        if 'Content-Length' not in self.headers:
            self.headers['Content-Length'] = str(len(self.content))

        if 'Content-Type' not in self.headers and self.media_type is not None:
            content_type = self.media_type
            if self.charset is not None:
                content_type += '; charset=%s' % self.charset
            self.headers['Content-Type'] = content_type


class HTMLResponse(Response):
    media_type = 'text/html'
    charset = 'utf-8'


class JSONResponse(Response):
    media_type = 'application/json'
    charset = None
    options = {
        'ensure_ascii': False,
        'allow_nan': False,
        'indent': None,
        'separators': (',', ':'),
    }

    def render(self, content: typing.Any) -> bytes:
        options = {'default': self.default}
        options.update(self.options)
        return json.dumps(content, **options).encode('utf-8')

    def default(self, obj: typing.Any) -> typing.Any:
        if isinstance(obj, types.Type):
            return dict(obj)
        error = "Object of type '%s' is not JSON serializable."
        raise TypeError(error % type(obj).__name__)
