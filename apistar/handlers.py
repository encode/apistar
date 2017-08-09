import base64
import typing

import coreapi
import coreschema

from apistar import Response, exceptions
from apistar.interfaces import Schema, StaticFiles, Templates, WSGIEnviron
from apistar.routing import PathWildcard


def api_documentation(schema: Schema, templates: Templates) -> Response:
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


def corejson_schema(schema: Schema) -> Response:
    codec = coreapi.codecs.CoreJSONCodec()
    content = codec.encode(schema)
    return Response(content, content_type='application/coreapi+json')


def javascript_schema(schema: Schema, templates: Templates) -> Response:
    codec = coreapi.codecs.CoreJSONCodec()
    base64_schema = base64.b64encode(codec.encode(schema)).decode('latin1')
    template = templates.get_template('apistar/schema.js')
    content = template.render(base64_schema=base64_schema).encode('utf-8')
    return Response(content, content_type='application/javascript')


def serve_static(path: PathWildcard, statics: StaticFiles, environ: WSGIEnviron):
    static_file = statics.get_file(path)
    if static_file is None:
        raise exceptions.NotFound()
    return static_file.get_response(environ)


setattr(api_documentation, 'exclude_from_schema', True)
setattr(corejson_schema, 'exclude_from_schema', True)
setattr(javascript_schema, 'exclude_from_schema', True)
setattr(serve_static, 'exclude_from_schema', True)
