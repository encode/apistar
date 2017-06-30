from typing import Any, Callable, Dict, List, Tuple, TypeVar, Union  # noqa
from urllib.parse import quote

from werkzeug.datastructures import Headers as WerkzeugHeaders
from werkzeug.datastructures import (
    EnvironHeaders, ImmutableDict, ImmutableHeadersMixin, ImmutableMultiDict
)
from werkzeug.formparser import parse_form_data
from werkzeug.http import parse_options_header
from werkzeug.urls import url_decode
from werkzeug.wsgi import get_input_stream

from apistar import exceptions
from apistar.compat import json
from apistar.core import ArgName
from apistar.schema import validate


class WSGIEnviron(ImmutableDict):
    pass


class Method(str):
    @classmethod
    def build(cls, environ: WSGIEnviron) -> "Method":
        return cls(environ['REQUEST_METHOD'])


class Scheme(str):
    @classmethod
    def build(cls, environ: WSGIEnviron) -> "Scheme":
        return cls(environ['wsgi.url_scheme'])


class Host(str):
    @classmethod
    def build(cls, environ: WSGIEnviron) -> "Host":
        return cls(environ.get('HTTP_HOST') or environ['SERVER_NAME'])


class Port(int):
    @classmethod
    def build(cls, environ: WSGIEnviron) -> "Port":
        if environ['wsgi.url_scheme'] == 'https':
            return cls(environ.get('SERVER_PORT') or 443)
        return cls(environ.get('SERVER_PORT') or 80)


class MountPath(str):
    @classmethod
    def build(cls, environ: WSGIEnviron) -> "MountPath":
        return cls(quote(environ.get('SCRIPT_NAME', '')))


class RelativePath(str):
    @classmethod
    def build(cls, environ: WSGIEnviron) -> "RelativePath":
        return cls(quote(environ.get('PATH_INFO', '')))


class Path(str):
    @classmethod
    def build(cls, environ: WSGIEnviron) -> "Path":
        path = environ.get('SCRIPT_NAME', '') + environ.get('PATH_INFO', '')
        return cls(quote(path))


class QueryString(str):
    @classmethod
    def build(cls, environ: WSGIEnviron) -> "QueryString":
        query_string = environ.get('QUERY_STRING', '')
        return cls(query_string)


class URL(str):
    @classmethod
    def build(cls, environ: WSGIEnviron) -> "URL":
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
    def build(cls, environ: WSGIEnviron) -> "Body":
        return get_input_stream(environ).read()


class Headers(ImmutableHeadersMixin, WerkzeugHeaders):
    def __init__(self, *args: Any, **kwargs: Dict[str, Any]) -> None:
        if len(args) == 1 and isinstance(args[0], dict):
            args = [list(args[0].items())]
        super().__init__(*args, **kwargs)

    @classmethod
    def build(cls, environ: WSGIEnviron) -> "Headers":
        return cls(EnvironHeaders(environ))


class Header(str):
    @classmethod
    def build(cls, headers: Headers, arg_name: ArgName) -> "Header":
        return headers.get(arg_name.replace('_', '-'))


class QueryParams(ImmutableMultiDict):
    @classmethod
    def build(cls, environ: WSGIEnviron) -> "QueryParams":
        query_string = environ.get('QUERY_STRING', '')
        return cls(url_decode(query_string))


class QueryParam(str):
    schema = None  # type: type

    @classmethod
    def build(cls, params: QueryParams, arg_name: ArgName) -> "QueryParam":
        value = params.get(arg_name)
        if value is None or cls.schema is None:
            return value
        if not isinstance(value, cls.schema):
            value = validate(cls.schema, value, key=arg_name)
        return value


HeadersType = Union[
    List[Tuple[str, str]],
    Dict[str, str],
    Headers
]


ResponseData = TypeVar('ResponseData')


class RequestData(object):
    schema = None  # type: type

    @classmethod
    def build(cls, environ: WSGIEnviron) -> Union[Dict, type]:
        if not bool(environ.get('CONTENT_TYPE')):
            mimetype = None
        else:
            mimetype, _ = parse_options_header(environ['CONTENT_TYPE'])

        if mimetype is None:
            value = None
        elif mimetype == 'application/json':
            body = get_input_stream(environ).read()
            value = json.loads(body.decode('utf-8'))
        elif mimetype in ('multipart/form-data', 'application/x-www-form-urlencoded'):
            stream, form, files = parse_form_data(environ)
            value = ImmutableMultiDict(list(form.items()) + list(files.items()))
        else:
            raise exceptions.UnsupportedMediaType()

        if cls.schema is None:
            return value
        if not isinstance(value, cls.schema):
            value = validate(cls.schema, value)
        return value


class RequestField(object):
    schema = None  # type: type

    @classmethod
    def build(cls, data: RequestData, arg_name: ArgName) -> Union[type, None]:
        value = data[arg_name]  # type: ignore

        if value is None or cls.schema is None:
            return value
        if not isinstance(value, cls.schema):
            value = validate(cls.schema, value, key=arg_name)
        return value


class Request(object):
    __slots__ = ('method', 'url', 'headers')

    def __init__(self, method: str, url: str, headers: HeadersType=None) -> None:
        self.method = method
        self.url = url
        self.headers = Headers(headers)

    @classmethod
    def build(cls,
              method: Method,
              url: URL,
              headers: Headers) -> "Request":
        return cls(method=method, url=url, headers=headers)


class Response(object):
    __slots__ = ('data', 'content', 'status', 'headers')

    def __init__(self,
                 data: Any,
                 status: int=None,
                 headers: HeadersType=None) -> None:
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
            if content:
                content_type = 'text/html; charset=utf-8'
            else:
                content_type = None
        elif isinstance(data, bytes):
            content = data
            if content:
                content_type = 'text/html; charset=utf-8'
            else:
                content_type = None
        else:
            content = json.dumps(data).encode('utf-8')
            content_type = 'application/json'

        if 'Content-Length' not in headers_dict:
            headers_list += [('Content-Length', str(len(content)))]
        if content_type and 'Content-Type' not in headers_dict:
            headers_list += [('Content-Type', content_type)]

        if status is None:
            status = 200 if content_type else 204

        self.data = data
        self.content = content
        self.status = status
        self.headers = Headers(headers_list)

    @classmethod
    def build(cls, data: ResponseData) -> "Response":
        return cls(data=data)
