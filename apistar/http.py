from typing import Any, Callable, Dict, List, Tuple, TypeVar, Union  # noqa
from urllib.parse import quote

from werkzeug.datastructures import Headers as WerkzeugHeaders
from werkzeug.datastructures import (
    EnvironHeaders, ImmutableDict, ImmutableHeadersMixin, ImmutableMultiDict
)
from werkzeug.urls import url_decode

import ujson as json
from apistar.pipelines import ArgName


class WSGIEnviron(ImmutableDict):
    pass


class Method(str):
    @classmethod
    def build(cls, environ: WSGIEnviron) -> 'Method':
        return cls(environ['REQUEST_METHOD'])


class Scheme(str):
    @classmethod
    def build(cls, environ: WSGIEnviron) -> 'Scheme':
        return cls(environ['wsgi.url_scheme'])


class Host(str):
    @classmethod
    def build(cls, environ: WSGIEnviron) -> 'Host':
        return cls(environ.get('HTTP_HOST') or environ['SERVER_NAME'])


class Port(int):
    @classmethod
    def build(cls, environ: WSGIEnviron) -> 'Port':
        if environ['wsgi.url_scheme'] == 'https':
            return cls(environ.get('SERVER_PORT') or 443)
        return cls(environ.get('SERVER_PORT') or 80)


class RootPath(str):
    @classmethod
    def build(cls, environ: WSGIEnviron) -> 'RootPath':
        return cls(quote(environ.get('SCRIPT_NAME', '')))


class Path(str):
    @classmethod
    def build(cls, environ: WSGIEnviron) -> 'Path':
        return cls(quote(environ.get('PATH_INFO', '')))


class QueryString(str):
    @classmethod
    def build(cls, environ: WSGIEnviron) -> 'QueryString':
        return cls(environ['QUERY_STRING'])


class URL(str):
    @classmethod
    def build(cls, environ: WSGIEnviron) -> 'URL':
        # https://www.python.org/dev/peps/pep-0333/#url-reconstruction
        url = environ['wsgi.url_scheme'] + '://'

        if environ.get('HTTP_HOST'):
            url += environ['HTTP_HOST']
        else:
            url += environ['SERVER_NAME']

            if environ['wsgi.url_scheme'] == 'https':
                if environ['SERVER_PORT'] != '443':
                    url += ':' + environ['SERVER_PORT']
            else:
                if environ['SERVER_PORT'] != '80':
                    url += ':' + environ['SERVER_PORT']

        url += quote(environ.get('SCRIPT_NAME', ''))
        url += quote(environ.get('PATH_INFO', ''))
        if environ.get('QUERY_STRING'):
            url += '?' + environ['QUERY_STRING']

        return cls(url)


class Body(bytes):
    @classmethod
    def build(cls, environ: WSGIEnviron) -> 'Body':
        return environ['wsgi.input'].read()


class Headers(ImmutableHeadersMixin, WerkzeugHeaders):
    @classmethod
    def build(cls, environ: WSGIEnviron) -> 'Headers':
        return cls(EnvironHeaders(environ))


class Header(str):
    @classmethod
    def build(cls, headers: Headers, arg_name: ArgName) -> 'Header':
        return headers.get(arg_name.replace('_', '-'))


class QueryParams(ImmutableMultiDict):
    @classmethod
    def build(cls, environ: WSGIEnviron) -> 'QueryParams':
        return cls(url_decode(environ['QUERY_STRING']))


class QueryParam(str):
    schema = None  # type: Callable

    @classmethod
    def build(cls, params: QueryParams, arg_name: ArgName) -> 'QueryParam':
        value = params.get(arg_name)
        if value is None or cls.schema is None:
            return value
        if not isinstance(value, cls.schema):
            value = cls.schema(value)
        return value


HeadersType = Union[
    List[Tuple[str, str]],
    Dict[str, str],
    Headers
]


ResponseData = TypeVar('ResponseData')


class Request(object):
    __slots__ = ('method', 'url', 'headers')

    def __init__(self, method: str, url: str, headers: HeadersType=None) -> None:
        if isinstance(headers, dict):
            headers = list(headers.items())
        self.method = method
        self.url = url
        self.headers = Headers(headers)

    @classmethod
    def build(cls, method: Method, url: URL, headers: Headers) -> 'Request':
        return cls(method=method, url=url, headers=headers)


class Response(object):
    __slots__ = ('data', 'content', 'status', 'headers')

    def __init__(self, data: Any, status: int=200, headers: HeadersType=None) -> None:
        if isinstance(headers, dict):
            headers = list(headers.items())
        self.data = data
        self.content = json.dumps(data).encode('utf-8')
        self.status = status
        self.headers = Headers(headers)

    @classmethod
    def build(cls, data: ResponseData) -> 'Response':
        return cls(data=data)
