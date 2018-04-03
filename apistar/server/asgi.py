import typing
from inspect import Parameter
from urllib.parse import parse_qsl

from apistar import http
from apistar.server.components import Component

ASGIScope = typing.NewType('ASGIScope', dict)
ASGIReceive = typing.NewType('ASGIReceive', typing.Callable)
ASGISend = typing.NewType('ASGISend', typing.Callable)


class MethodComponent(Component):
    def resolve(self,
                scope: ASGIScope) -> http.Method:
        return http.Method(scope['method'])


class URLComponent(Component):
    def resolve(self,
                scope: ASGIScope) -> http.URL:
        scheme = scope['scheme']
        host, port = scope['server']
        path = scope['path']

        if (scheme == 'http' and port != 80) or (scheme == 'https' and port != 443):
            url = '%s://%s:%s%s' % (scheme, host, port, path)
        else:
            url = '%s://%s%s' % (scheme, host, path)

        query_string = scope['query_string']
        if query_string:
            url += '?' + query_string.decode()

        return http.URL(url)


class SchemeComponent(Component):
    def resolve(self,
                scope: ASGIScope) -> http.Scheme:
        return http.Scheme(scope['scheme'])


class HostComponent(Component):
    def resolve(self,
                scope: ASGIScope) -> http.Host:
        return http.Host(scope['server'][0])


class PortComponent(Component):
    def resolve(self,
                scope: ASGIScope) -> http.Port:
        return http.Port(scope['server'][1])


class PathComponent(Component):
    def resolve(self,
                scope: ASGIScope) -> http.Path:
        return http.Path(scope.get('root_path', '') + scope['path'])


class QueryStringComponent(Component):
    def resolve(self,
                scope: ASGIScope) -> http.QueryString:
        return http.QueryString(scope['query_string'].decode())


class QueryParamsComponent(Component):
    def resolve(self,
                scope: ASGIScope) -> http.QueryParams:
        query_string = scope['query_string'].decode()
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
                scope: ASGIScope) -> http.Headers:
        return http.Headers([
            (key.decode(), value.decode())
            for key, value in scope['headers']
        ])


class HeaderComponent(Component):
    def resolve(self,
                parameter: Parameter,
                headers: http.Headers) -> http.Header:
        name = parameter.name.replace('_', '-')
        if name not in headers:
            return None
        return http.Header(headers[name])


class BodyComponent(Component):
    async def resolve(self,
                      receive: ASGIReceive) -> http.Body:
        body = b''
        while True:
            message = await receive()
            if not message['type'] == 'http.request':
                error = "'Unexpected ASGI message type '%s'."
                raise Exception(error % message['type'])
            body += message.get('body', b'')
            if not message.get('more_body', False):
                break

        return http.Body(body)


class RequestComponent(Component):
    def resolve(self,
                method: http.Method,
                url: http.URL,
                headers: http.Headers,
                body: http.Body) -> http.Request:
        return http.Request(method, url, headers, body)


ASGI_COMPONENTS = (
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
