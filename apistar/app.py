from apistar.interfaces import *
from apistar.components import common, dependency, routing, statics, templates, wsgi
from apistar.schema import get_schema
import typing
import werkzeug


REQUIRED_STATE = {
    'wsgi_environ': WSGIEnviron,
    'path': Path,
    'method': Method,
    'url_args': URLArgs,
    'router': Router
}  # type: typing.Dict[str, type]

PROVIDERS = {
    # WSGI
    Headers: wsgi.get_headers,
    QueryParams: wsgi.get_queryparams,
    Body: wsgi.get_body,
    # Common
    Header: common.lookup_header,
    QueryParam: common.lookup_queryparam,
    URLArg: common.lookup_url_arg,
    # Schemas
    Schema: get_schema,
    Templates: templates.Jinja2Templates,
    StaticFiles: statics.WhiteNoiseStaticFiles
}  # type: typing.Dict[type, typing.Callable]


class App():
    def __init__(self, routes: typing.Sequence[Route]) -> None:
        self.router = routing.WerkzeugRouter(routes)
        self.injector = dependency.DependencyInjector(PROVIDERS, REQUIRED_STATE)

    def __call__(self, environ: typing.Dict[str, typing.Any], start_response: typing.Callable):
        method = environ['REQUEST_METHOD'].upper()
        path = environ['SCRIPT_NAME'] + environ['PATH_INFO']
        try:
            view, url_args = self.router.lookup(path, method)
        except werkzeug.exceptions.HTTPException as exc:
            response = exc.get_response(environ)
        else:
            state = {
                'wsgi_environ': environ,
                'path': path,
                'method': method,
                'router': self.router,
                'url_args': url_args
            }
            response = self.injector.run(view, state=state)
        return response(environ, start_response)

    def run(self, hostname: str='localhost', port: int=8080, **options) -> None:
        werkzeug.run_simple(hostname, port, self, **options)
