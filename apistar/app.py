import json
import typing

import werkzeug

from apistar import exceptions, http, routing
from apistar.components import (
    dependency, router, schema, statics, templates, wsgi
)
from apistar.interfaces import (
    Injector, Router, Schema, Settings, StaticFiles, Templates, URLArgs,
    WSGIEnviron
)

REQUIRED_STATE = {
    'wsgi_environ': WSGIEnviron,
    'path': http.Path,
    'method': http.Method,
    'url_args': URLArgs,
    'router': Router,
    'settings': Settings,
    'exc': Exception
}  # type: typing.Dict[str, type]


DEFAULT_COMPONENTS = {
    # HTTP Components
    http.URL: wsgi.get_url,
    http.Scheme: wsgi.get_scheme,
    http.Host: wsgi.get_host,
    http.Port: wsgi.get_port,
    http.Headers: wsgi.get_headers,
    http.Header: wsgi.get_header,
    http.QueryString: wsgi.get_querystring,
    http.QueryParams: wsgi.get_queryparams,
    http.QueryParam: wsgi.get_queryparam,
    http.Body: wsgi.get_body,
    http.RequestData: wsgi.get_request_data,
    # Framework Components
    Schema: schema.CoreAPISchema,
    Templates: templates.Jinja2Templates,
    StaticFiles: statics.WhiteNoiseStaticFiles,
    Router: router.WerkzeugRouter,
    Injector: dependency.DependencyInjector
}  # type: typing.Dict[type, typing.Callable]


class App():
    def __init__(self,
                 routes: routing.Routes,
                 components: typing.Dict[type, typing.Callable]=None,
                 settings: typing.Dict[str, typing.Any]=None) -> None:
        if components is None:
            components = {}
        if settings is None:
            settings = {}

        components = {**DEFAULT_COMPONENTS, **components}
        router_cls = components.pop(Router)
        injector_cls = components.pop(Injector)

        self.routes = routes
        self.settings = settings
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
            'settings': self.settings,
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

        if isinstance(exc, exceptions.HTTPException):
            if isinstance(exc.detail, str):
                content = {'message': exc.detail}
            else:
                content = exc.detail
            return http.Response(content, exc.status_code, {})

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

        if 'Content-Type' in headers:
            content_type = None

        return werkzeug.Response(content, status, headers, content_type=content_type)

    def run(self, hostname: str='localhost', port: int=8080, **options) -> None:  # pragma: nocover
        werkzeug.run_simple(hostname, port, self, **options)
