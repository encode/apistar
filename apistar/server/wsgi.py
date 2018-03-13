import typing
from inspect import Parameter
from wsgiref.util import request_uri

from werkzeug.urls import url_decode
from werkzeug.wsgi import get_input_stream

from apistar.server import http
from apistar.server.injector import Component

WSGIEnviron = typing.NewType('WSGIEnviron', dict)


class MethodComponent(Component):
    resolves = [http.Method]

    def resolve_parameter(self, environ: WSGIEnviron):
        return environ['REQUEST_METHOD'].upper()


class URLComponent(Component):
    resolves = [http.URL]

    def resolve_parameter(self, environ: WSGIEnviron):
        return http.URL(request_uri(environ))


class SchemeComponent(Component):
    resolves = [http.Scheme]

    def resolve_parameter(self, environ: WSGIEnviron):
        return environ['wsgi.url_scheme']


class HostComponent(Component):
    resolves = [http.Host]

    def resolve_parameter(self, environ: WSGIEnviron) -> str:
        return environ.get('HTTP_HOST') or environ['SERVER_NAME']


class PortComponent(Component):
    resolves = [http.Port]

    def resolve_parameter(self, environ: WSGIEnviron):
        if environ['wsgi.url_scheme'] == 'https':
            return int(environ.get('SERVER_PORT') or 443)
        return int(environ.get('SERVER_PORT') or 80)


class PathComponent(Component):
    resolves = [http.Path]

    def resolve_parameter(self, environ: WSGIEnviron):
        return environ['SCRIPT_NAME'] + environ['PATH_INFO']


class QueryStringComponent(Component):
    resolves = [http.QueryString]

    def resolve_parameter(self, environ: WSGIEnviron):
        return environ.get('QUERY_STRING', '')


class QueryParamsComponent(Component):
    resolves = [http.QueryParams]

    def resolve_parameter(self, environ: WSGIEnviron):
        return url_decode(
            environ.get('QUERY_STRING', ''),
            cls=http.QueryParams
        )


class QueryParamComponent(Component):
    resolves = [http.QueryParam]

    def resolve_parameter(self, parameter: Parameter, query_params: http.QueryParams):
        name = parameter.name
        return query_params.get(name)


class HeadersComponent(Component):
    resolves = [http.Headers]

    def resolve_parameter(self, environ: WSGIEnviron):
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
    resolves = [http.Header]

    def resolve_parameter(self, parameter: Parameter, headers: http.Headers):
        name = parameter.name
        return headers.get(name.replace('_', '-'))


class BodyComponent(Component):
    resolves = [http.Body]

    def resolve_parameter(self, environ: WSGIEnviron):
        return get_input_stream(environ).read()


class RequestComponent(Component):
    resolves = [http.Request]

    def resolve_parameter(self, method: http.Method, url: http.URL, headers: http.Headers, body: http.Body):
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
