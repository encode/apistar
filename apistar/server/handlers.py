from apistar import App, http
from apistar.codecs import OpenAPICodec


def serve_schema(app: App):
    codec = OpenAPICodec()
    content = codec.encode(app.document)
    headers = {'Content-Type': 'application/vnd.oai.openapi'}
    return http.Response(content, headers=headers)


def serve_documentation(app: App):
    template_name = 'apistar/docs/index.html'
    return app.render_template(template_name, document=app.document)
