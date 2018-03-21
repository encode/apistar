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
        return Response({'msg':exc.detail}, exc.status_code, exc.get_headers())
    raise


class App():
    def __init__(self, document, template_dir=None, template_apps=None, components=None):
        components = list(components) if components else []

        self.document = document
        self.router = self.init_router(document)
        self.templates = self.init_templates(template_dir, template_apps)
        self.injector = self.init_injector(components)
        self.exception_handler = exception_handler

    def init_router(self, document):
        return Router(document)

    def init_templates(self, template_dir: str=None, template_apps: list=None):
        return Templates(template_dir, template_apps, {
            'reverse_url': self.reverse_url,
            'static_url': self.static_url
        })

    def init_injector(self, components=None):
        components = components if components else []
        components = list(WSGI_COMPONENTS + VALIDATION_COMPONENTS) + components
        initial_components = {
            'environ': WSGIEnviron,
            'exc': Exception,
            'app': App,
            'path_params': PathParams,
            'link': Link
        }
        return Injector(components, initial_components)

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
