from apistar.interfaces import PathWildcard, Schema, StaticFiles, Templates, WSGIEnviron
import base64
import coreapi
import coreschema
import typing
import werkzeug


def api_documentation(schema: Schema, templates: Templates):
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
    return werkzeug.Response(content, content_type='text/html')


def corejson_schema(schema: Schema):
    codec = coreapi.codecs.CoreJSONCodec()
    content = codec.encode(schema)
    headers = {'Content-Type': codec.media_type}
    return werkzeug.Response(content, headers=headers)


def javascript_schema(schema: Schema, templates: Templates):
    codec = coreapi.codecs.CoreJSONCodec()
    base64_schema = base64.b64encode(codec.encode(schema)).decode('latin1')
    template = templates.get_template('apistar/schema.js')
    content = template.render(base64_schema=base64_schema).encode('utf-8')
    headers = {'Content-Type': 'application/javascript'}
    return werkzeug.Response(content, headers=headers)


def serve_static(path: PathWildcard, statics: StaticFiles, environ: WSGIEnviron):
    static_file = statics.get_file(path)
    if static_file is None:
        raise werkzeug.exceptions.NotFound()
    return static_file.get_response(environ)


setattr(api_documentation, 'exclude_from_schema', True)
setattr(corejson_schema, 'exclude_from_schema', True)
setattr(javascript_schema, 'exclude_from_schema', True)
setattr(serve_static, 'exclude_from_schema', True)
