from apistar import exceptions
from apistar.document import Link
from apistar.http import RESPONSE_STATUS_TEXT, PathParams, Response
from apistar.server.injector import Injector
from apistar.server.router import Router
from apistar.server.templates import Templates
from apistar.server.validation import VALIDATION_COMPONENTS
from apistar.server.wsgi import WSGI_COMPONENTS, WSGIEnviron
from apistar.utils import encode_json


def exception_handler(exc: Exception) -> Response:
    if isinstance(exc, exceptions.HTTPException):
        return Response(exc.detail, exc.status_code, exc.get_headers())
    raise


class App():
    def __init__(self, document, components=None):
        components = list(components) if components else []

        self.document = document
        self.components = self.default_components() + components
        self.router = self.default_router()
        self.templates = self.default_templates()
        self.injector = self.default_injector()
        self.exception_handler = exception_handler

    def get_initial_components(self):
        return {
            'environ': WSGIEnviron,
            'exc': Exception,
            'app': App,
            'path_params': PathParams,
            'link': Link
        }

    def default_components(self):
        return list(WSGI_COMPONENTS + VALIDATION_COMPONENTS)

    def default_router(self):
        return Router(self.document)

    def default_templates(self):
        return Templates(self)

    def default_injector(self):
        initial_components = self.get_initial_components()
        return Injector(self.components, initial_components)

    def reverse_url(self, name: str, **params):
        return self.router.reverse_url(name, **params)

    def render_template(self, path: str, **context):
        return self.templates.render_template(path, **context)

    def static_url(self, path: str):
        return '#'

    def render_response(self, response):
        if isinstance(response, Response):
            return response

        if isinstance(response, str):
            content = response.encode('utf-8')
            headers = {'Content-Type': 'text/html; charset=utf-8'}
            return Response(content, headers=headers)

        content = encode_json(response)
        headers = {'Content-Type': 'application/json'}
        return Response(content, headers=headers)

    def __call__(self, environ, start_response):
        state = {
            'environ': environ,
            'exc': None,
            'app': self,
            'path_params': None,
            'link': None
        }
        method = environ['REQUEST_METHOD'].upper()
        path = environ['PATH_INFO']
        try:
            link, handler, path_params = self.router.lookup(path, method)
            state['link'] = link
            state['path_params'] = path_params
            response = self.injector.run(handler, state)
        except Exception as exc:
            state['exc'] = exc
            response = self.injector.run(self.exception_handler, state)

        response = self.render_response(response)

        # Get the WSGI response information, given the Response instance.
        try:
            status_text = RESPONSE_STATUS_TEXT[response.status_code]
        except KeyError:
            status_text = str(response.status_code)

        if isinstance(response.content, str):
            content = [response.content.encode('utf-8')]
        elif isinstance(response.content, bytes):
            content = [response.content]
        else:
            content = [encode_json(response.content)]

        # Return the WSGI response.
        start_response(status_text, list(response.headers))
        return content
