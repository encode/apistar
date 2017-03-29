from apistar.pipelines import ArgName
from typing import Dict, Any, Union, List, Tuple, TypeVar
from urllib.parse import quote
from werkzeug.datastructures import (
    EnvironHeaders, Headers as WerkzeugHeaders,
    ImmutableDict, ImmutableMultiDict, ImmutableHeadersMixin
)
from werkzeug.urls import url_decode
import json


class WSGIEnviron(ImmutableDict):
    pass


class Method(str):
    @classmethod
    def build(cls, environ: WSGIEnviron):
        return cls(environ['REQUEST_METHOD'])


class Scheme(str):
    @classmethod
    def build(cls, environ: WSGIEnviron):
        return cls(environ['wsgi.url_scheme'])


class Host(str):
    @classmethod
    def build(cls, environ: WSGIEnviron):
        return cls(environ.get('HTTP_HOST') or environ['SERVER_NAME'])


class Port(int):
    @classmethod
    def build(cls, environ: WSGIEnviron):
        if environ['wsgi.url_scheme'] == 'https':
            return cls(environ.get('SERVER_PORT') or 443)
        return cls(environ.get('SERVER_PORT') or 80)


class RootPath(str):
    @classmethod
    def build(cls, environ: WSGIEnviron):
        return cls(quote(environ.get('SCRIPT_NAME', '')))


class Path(str):
    @classmethod
    def build(cls, environ: WSGIEnviron):
        return cls(quote(environ.get('PATH_INFO', '')))


class QueryString(str):
    @classmethod
    def build(cls, environ: WSGIEnviron):
        return cls(environ['QUERY_STRING'])


class URL(str):
    @classmethod
    def build(cls, environ: WSGIEnviron):
        # https://www.python.org/dev/peps/pep-0333/#url-reconstruction
        url = environ['wsgi.url_scheme']+'://'

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


class Headers(ImmutableHeadersMixin, WerkzeugHeaders):
    @classmethod
    def build(cls, environ: WSGIEnviron):
        return cls(EnvironHeaders(environ))


class QueryParams(ImmutableMultiDict):
    @classmethod
    def build(cls, environ: WSGIEnviron):
        return cls(url_decode(environ['QUERY_STRING']))


class NamedHeader(str):
    @classmethod
    def build(cls, headers: Headers, arg_name: ArgName):
        return headers.get(arg_name.replace('_', '-'))


class NamedQueryParam(str):
    @classmethod
    def build(cls, params: QueryParams, arg_name: ArgName):
        return params.get(arg_name)


HeadersType = Union[
    List[Tuple[str, str]],
    Dict[str, str],
    Headers
]


ResponseData = TypeVar('ResponseData')


class Request(object):
    __slots__ = ('method', 'url', 'headers')

    def __init__(self, method: str, url: str, headers: HeadersType=None):
        if isinstance(headers, dict):
            headers = list(headers.items())
        self.method = method
        self.url = url
        self.headers = Headers(headers)

    @classmethod
    def build(cls, method: Method, url: URL, headers: Headers):
        return cls(method=method, url=url, headers=headers)


class Response(object):
    __slots__ = ('data', 'content', 'status', 'headers')

    def __init__(self, data: Any, status: int=200, headers: HeadersType=None):
        if isinstance(headers, dict):
            headers = list(headers.items())
        self.data = data
        self.content = json.dumps(data).encode('utf-8')
        self.status = status
        self.headers = Headers(headers)

    @classmethod
    def build(cls, data: ResponseData):
        return cls(data=data)
