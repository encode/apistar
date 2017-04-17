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


class MountPath(str):
    @classmethod
    def build(cls, environ: WSGIEnviron):
        return cls(quote(environ.get('SCRIPT_NAME', '')))


class RelativePath(str):
    @classmethod
    def build(cls, environ: WSGIEnviron):
        return cls(quote(environ.get('PATH_INFO', '')))


class Path(str):
    @classmethod
    def build(cls, environ: WSGIEnviron):
        path = environ.get('SCRIPT_NAME', '') + environ.get('PATH_INFO', '')
        return cls(quote(path))


class QueryString(str):
    @classmethod
    def build(cls, environ: WSGIEnviron):
        return cls(environ['QUERY_STRING'])


class URL(str):
    @classmethod
    def build(cls, environ: WSGIEnviron):
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
    def build(cls, environ: WSGIEnviron):
        return environ['wsgi.input'].read()


class Headers(ImmutableHeadersMixin, WerkzeugHeaders):
    @classmethod
    def build(cls, environ: WSGIEnviron):
        return cls(EnvironHeaders(environ))


class Header(str):
    @classmethod
    def build(cls, headers: Headers, arg_name: ArgName):
        return headers.get(arg_name.replace('_', '-'))


class QueryParams(ImmutableMultiDict):
    @classmethod
    def build(cls, environ: WSGIEnviron):
	if 'QUERY_STRING' not in environ:
	    return cls(None)
        return cls(url_decode(environ['QUERY_STRING']))


class QueryParam(str):
    schema = None  # type: type

    @classmethod
    def build(cls, params: QueryParams, arg_name: ArgName):
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
    def build(cls, method: Method, url: URL, headers: Headers):
        return cls(method=method, url=url, headers=headers)


class Response(object):
    __slots__ = ('data', 'content', 'status', 'headers')

    def __init__(self, data: Any, status: int=200, headers: HeadersType=None) -> None:
        if headers is None:
            headers_dict = {}  # type: Union[Dict[str, str], Headers]
            headers_list = []  # type: List[Tuple[str, str]]
        elif isinstance(headers, dict):
            headers_dict = headers
            headers_list = list(headers.items())
        elif isinstance(headers, list):
            headers_dict = dict(headers)
            headers_list = headers
        else:
            headers_dict = headers
            headers_list = headers.to_list()

        if isinstance(data, str):
            content = data.encode('utf-8')
            content_type = 'text/html; charset=utf-8'
        elif isinstance(data, bytes):
            content = data
            content_type = 'text/html; charset=utf-8'
        else:
            content = json.dumps(data).encode('utf-8')
            content_type = 'application/json'

        if 'Content-Length' not in headers_dict:
            headers_list += [('Content-Length', str(len(content)))]
        if 'Content-Type' not in headers_dict:
            headers_list += [('Content-Type', content_type)]

        self.data = data
        self.content = content
        self.status = status
        self.headers = Headers(headers_list)

    @classmethod
    def build(cls, data: ResponseData):
        return cls(data=data)
