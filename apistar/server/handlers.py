from apistar import App, http
from apistar.codecs import OpenAPICodec


def serve_schema(app: App):
    codec = OpenAPICodec()
    content = codec.encode(app.document)
    return http.Response(content)
