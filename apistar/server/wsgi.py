import typing
from http import HTTPStatus
from inspect import Parameter
from urllib.parse import parse_qsl
from wsgiref.util import request_uri

from werkzeug.wsgi import get_input_stream

from apistar import http
from apistar.server.components import Component

WSGIEnviron = typing.NewType('WSGIEnviron', dict)
WSGIStartResponse = typing.NewType('WSGIStartResponse', typing.Callable)


RESPONSE_STATUS_TEXT = {
    code: str(code) for code in range(100, 600)
}
RESPONSE_STATUS_TEXT.update({
    status.value: "%d %s" % (status.value, status.phrase)
    for status in HTTPStatus
})


class MethodComponent(Component):
    def resolve(self,
                environ: WSGIEnviron) -> http.Method:
        return http.Method(environ['REQUEST_METHOD'].upper())


class URLComponent(Component):
    def resolve(self,
                environ: WSGIEnviron) -> http.URL:
        return http.URL(request_uri(environ))


class SchemeComponent(Component):
    def resolve(self,
                environ: WSGIEnviron) -> http.Scheme:
        return http.Scheme(environ['wsgi.url_scheme'])


class HostComponent(Component):
    def resolve(self,
                environ: WSGIEnviron) -> http.Host:
        return http.Host(environ.get('HTTP_HOST') or environ['SERVER_NAME'])


class PortComponent(Component):
    def resolve(self,
                environ: WSGIEnviron) -> http.Port:
        if environ['wsgi.url_scheme'] == 'https':
            return http.Port(int(environ.get('SERVER_PORT', 443)))
        return http.Port(int(environ.get('SERVER_PORT', 80)))


class PathComponent(Component):
    def resolve(self,
                environ: WSGIEnviron) -> http.Path:
        return http.Path(environ['SCRIPT_NAME'] + environ['PATH_INFO'])


class QueryStringComponent(Component):
    def resolve(self,
                environ: WSGIEnviron) -> http.QueryString:
        return http.QueryString(environ.get('QUERY_STRING', ''))


class QueryParamsComponent(Component):
    def resolve(self,
                environ: WSGIEnviron) -> http.QueryParams:
        query_string = environ.get('QUERY_STRING', '')
        return http.QueryParams(parse_qsl(query_string))


class QueryParamComponent(Component):
    def resolve(self,
                parameter: Parameter,
                query_params: http.QueryParams) -> http.QueryParam:
        name = parameter.name
        if name not in query_params:
            return None
        return http.QueryParam(query_params[name])


class HeadersComponent(Component):
    def resolve(self,
                environ: WSGIEnviron) -> http.Headers:
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
    def resolve(self,
                parameter: Parameter,
                headers: http.Headers) -> http.Header:
        name = parameter.name.replace('_', '-')
        if name not in headers:
            return None
        return http.Header(headers[name])


class BodyComponent(Component):
    def resolve(self,
                environ: WSGIEnviron) -> http.Body:
        return http.Body(get_input_stream(environ).read())


class RequestComponent(Component):
    def resolve(self,
                method: http.Method,
                url: http.URL,
                headers: http.Headers,
                body: http.Body) -> http.Request:
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
