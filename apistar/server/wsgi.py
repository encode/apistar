import typing
from inspect import Parameter
from urllib.parse import parse_qsl
from wsgiref.util import request_uri

from werkzeug.wsgi import get_input_stream

from apistar import http
from apistar.server.components import Component

WSGIEnviron = typing.NewType('WSGIEnviron', dict)


class MethodComponent(Component):
    resolves_types = (http.Method,)

    def resolve(self, environ: WSGIEnviron):
        return environ['REQUEST_METHOD'].upper()


class URLComponent(Component):
    resolves_types = (http.URL,)

    def resolve(self, environ: WSGIEnviron):
        return http.URL(request_uri(environ))


class SchemeComponent(Component):
    resolves_types = (http.Scheme,)

    def resolve(self, environ: WSGIEnviron):
        return environ['wsgi.url_scheme']


class HostComponent(Component):
    resolves_types = (http.Host,)

    def resolve(self, environ: WSGIEnviron):
        return environ.get('HTTP_HOST') or environ['SERVER_NAME']


class PortComponent(Component):
    resolves_types = (http.Port,)

    def resolve(self, environ: WSGIEnviron):
        if environ['wsgi.url_scheme'] == 'https':
            return int(environ.get('SERVER_PORT') or 443)
        return int(environ.get('SERVER_PORT') or 80)


class PathComponent(Component):
    resolves_types = (http.Path,)

    def resolve(self, environ: WSGIEnviron):
        return environ['SCRIPT_NAME'] + environ['PATH_INFO']


class QueryStringComponent(Component):
    resolves_types = (http.QueryString,)

    def resolve(self, environ: WSGIEnviron):
        return environ.get('QUERY_STRING', '')


class QueryParamsComponent(Component):
    resolves_types = (http.QueryParams,)

    def resolve(self, environ: WSGIEnviron):
        query_string = environ.get('QUERY_STRING', '')
        return http.QueryParams(parse_qsl(query_string))


class QueryParamComponent(Component):
    resolves_types = (http.QueryParam,)

    def resolve(self, parameter: Parameter, query_params: http.QueryParams):
        name = parameter.name
        return query_params.get(name)


class HeadersComponent(Component):
    resolves_types = (http.Headers,)

    def resolve(self, environ: WSGIEnviron):
        header_items = []
        for key, value in environ.items():
            if key.startswith('HTTP_'):
                header = (key[5:].lower().replace('_', '-'), value)
                header_items.append(header)
            elif key in ('CONTENT_TYPE', 'CONTENT_LENGTH'):
                header = (key.lower().replace('_', '-'), value)
                header_items.append(header)
        return http.Headers(header_items)


class HeaderComponent(Component):
    resolves_types = (http.Header,)

    def resolve(self, parameter: Parameter, headers: http.Headers):
        name = parameter.name
        return headers.get(name.replace('_', '-'))


class BodyComponent(Component):
    resolves_types = (http.Body,)

    def resolve(self, environ: WSGIEnviron):
        return get_input_stream(environ).read()


class RequestComponent(Component):
    resolves_types = (http.Request,)

    def resolve(self, method: http.Method, url: http.URL, headers: http.Headers, body: http.Body):
        return http.Request(method, url, headers, body)


WSGI_COMPONENTS = (
    MethodComponent(),
    URLComponent(),
    SchemeComponent(),
    HostComponent(),
    PortComponent(),
    PathComponent(),
    QueryStringComponent(),
    QueryParamsComponent(),
    QueryParamComponent(),
    HeadersComponent(),
    HeaderComponent(),
    BodyComponent(),
    RequestComponent()
)
