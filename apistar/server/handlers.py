from apistar import App, http
from apistar.codecs import OpenAPICodec


def serve_schema(app: App):
    document = app.document
    codec = OpenAPICodec()
    content = codec.encode(document)
    return http.Response(content)


def serve_documentation(app: App):
    document = app.document
    template_name = 'apistar/docs/index.html'
    content = app.render_template(template_name, document=document)
    return http.Response(content)
