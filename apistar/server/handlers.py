from apistar import App, http
from apistar.codecs import OpenAPICodec
from apistar.server.asgi import ASGIReceive, ASGIScope, ASGISend
from apistar.server.wsgi import WSGIEnviron, WSGIStartResponse


def serve_schema(app: App):
    codec = OpenAPICodec()
    content = codec.encode(app.document)
    headers = {'Content-Type': 'application/vnd.oai.openapi'}
    return http.Response(content, headers=headers)


def serve_documentation(app: App):
    template_name = 'apistar/docs/index.html'
    code_style = None  # pygments_css('emacs')
    return app.render_template(
        template_name, document=app.document, langs=['javascript', 'python'], code_style=code_style)


def serve_static_wsgi(app: App, environ: WSGIEnviron, start_response: WSGIStartResponse):
    return app.statics(environ, start_response)


async def serve_static_asgi(app: App, scope: ASGIScope, receive: ASGIReceive, send: ASGISend):
    instance = app.statics(scope)
    await instance(receive, send)
