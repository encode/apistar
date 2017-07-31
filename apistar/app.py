from apistar import exceptions, http
from apistar.interfaces import *
from apistar.components import common, dependency, routing, statics, templates, wsgi
from apistar.schema import get_schema
import typing
import json
import werkzeug


REQUIRED_STATE = {
    'wsgi_environ': WSGIEnviron,
    'path': http.Path,
    'method': http.Method,
    'url_args': URLArgs,
    'router': Router,
    'exc': Exception
}  # type: typing.Dict[str, type]


DEFAULT_COMPONENTS = {
    # WSGI
    http.URL: wsgi.get_url,
    http.Scheme: wsgi.get_scheme,
    http.Host: wsgi.get_host,
    http.Port: wsgi.get_port,
    http.Path: wsgi.get_path,
    http.Headers: wsgi.get_headers,
    http.QueryString: wsgi.get_querystring,
    http.QueryParams: wsgi.get_queryparams,
    http.Body: wsgi.get_body,
    http.RequestData: wsgi.get_request_data,
    # Common
    http.Header: common.lookup_header,
    http.QueryParam: common.lookup_queryparam,
    URLArg: common.lookup_url_arg,
    # Schemas
    Schema: get_schema,
    Templates: templates.Jinja2Templates,
    StaticFiles: statics.WhiteNoiseStaticFiles,
    Router: routing.WerkzeugRouter,
    Injector: dependency.DependencyInjector
}  # type: typing.Dict[type, typing.Callable]


class App():
    def __init__(self,
                 routes: typing.Sequence[Route],
                 components: typing.Dict[type, typing.Callable]={}) -> None:
        components = {**DEFAULT_COMPONENTS, **components}
        router_cls = components.pop(Router)
        injector_cls = components.pop(Injector)

        self.routes = routes
        self.router = router_cls(routes)
        self.injector = injector_cls(components, REQUIRED_STATE)

    def __call__(self, environ: typing.Dict[str, typing.Any], start_response: typing.Callable):
        method = environ['REQUEST_METHOD'].upper()
        path = environ['SCRIPT_NAME'] + environ['PATH_INFO']
        state = {
            'wsgi_environ': environ,
            'path': path,
            'method': method,
            'router': self.router,
            'url_args': None,
            'exc': None
        }
        try:
            view, url_args = self.router.lookup(path, method)
            state['url_args'] = url_args
            response = self.injector.run(view, state=state)
            response = self.finalize_response(response)
        except Exception as exc:
            state['exc'] = exc
            response = self.injector.run(self.exception_handler, state=state)
            response = self.finalize_response(response)

        return response(environ, start_response)

    def exception_handler(self, exc: Exception) -> http.Response:
        if isinstance(exc, exceptions.Found):
            return http.Response('', exc.status_code, {'Location': exc.location})

        if isinstance(exc, exceptions.APIException):
            if isinstance(exc.detail, str):
                content = {'message': exc.detail}
            else:
                content = exc.detail
            return http.Response(content, exc.status_code)

        raise

    def finalize_response(self, response):
        # TODO: We want to remove this in favor of more dynamic response types.
        if isinstance(response, werkzeug.Response):
            return response
        elif isinstance(response, http.Response):
            data, status, headers = response
        else:
            data, status, headers = response, 200, {}

        if data is None:
            content = b''
            content_type = 'text/plain'
        elif isinstance(data, str):
            content = data.encode('utf-8')
            content_type = 'text/html; charset=utf-8'
        elif isinstance(data, bytes):
            content = data
            content_type = 'text/html; charset=utf-8'
        else:
            content = json.dumps(data).encode('utf-8')
            content_type = 'application/json'

        if not content and status == 200:
            status = 204
            content_type = None

        return werkzeug.Response(content, status, headers, content_type=content_type)

    def run(self, hostname: str='localhost', port: int=8080, **options) -> None:
        werkzeug.run_simple(hostname, port, self, **options)
