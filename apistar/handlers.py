import base64
import typing

import coreapi
import coreschema

from apistar import Response, Route, annotate, exceptions, http
from apistar.interfaces import FileWrapper, Schema, StaticFiles, Templates
from apistar.types import PathWildcard


@annotate(authentication=None, permissions=None, exclude_from_schema=True)
def api_documentation(schema: Schema,
                      templates: Templates) -> Response:
    index = templates.get_template('apistar/docs/index.html')
    langs = ['python', 'javascript', 'shell']

    def render_form(link: coreapi.Link) -> str:
        properties = dict([
            (field.name, field.schema or coreschema.String())
            for field in link.fields
        ])
        required = []  # type: typing.List[str]
        schema = coreschema.Object(properties=properties, required=required)
        return coreschema.render_to_form(schema)

    def get_fields(link: coreapi.Link, location: str) -> typing.List[coreapi.Field]:
        return [
            field for field in link.fields
            if field.location == location
        ]

    content = index.render(
        document=schema,
        langs=langs,
        get_fields=get_fields,
        render_form=render_form
    ).encode('utf-8')
    return Response(content, content_type='text/html; charset=utf-8')


@annotate(authentication=None, permissions=None, exclude_from_schema=True)
def serve_schema(schema: Schema) -> Response:
    codec = coreapi.codecs.CoreJSONCodec()
    content = codec.encode(schema)
    return Response(content, content_type='application/coreapi+json')


@annotate(authentication=None, permissions=None, exclude_from_schema=True)
def javascript_schema(schema: Schema,
                      templates: Templates) -> Response:
    codec = coreapi.codecs.CoreJSONCodec()
    base64_schema = base64.b64encode(codec.encode(schema)).decode('latin1')
    template = templates.get_template('apistar/schema.js')
    content = template.render(base64_schema=base64_schema).encode('utf-8')
    return Response(content, content_type='application/javascript')


@annotate(authentication=None, permissions=None, exclude_from_schema=True)
def serve_static(statics: StaticFiles,
                 path: PathWildcard,
                 method: http.Method,
                 headers: http.Headers,
                 file_wrapper: FileWrapper) -> Response:
    static_file = statics.get_file(path)
    if static_file is None:
        raise exceptions.NotFound()
    return static_file.get_response(method, headers, file_wrapper)


docs_urls = [
    Route('/', 'GET', api_documentation),
    Route('/schema/', 'GET', serve_schema),
    Route('/schema.js', 'GET', javascript_schema),
]

static_urls = [
    Route('/{path}', 'GET', serve_static)
]
