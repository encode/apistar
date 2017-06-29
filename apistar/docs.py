import coreschema
from coreapi import Link

from apistar.apischema import APISchema, serve_schema, serve_schema_js
from apistar.decorators import exclude_from_schema
from apistar.http import Path
from apistar.routing import Route
from apistar.templating import Templates


def render_form(link: Link) -> str:
    properties = dict([
        (field.name, field.schema or coreschema.String())
        for field in link.fields
    ])
    required: list = []
    schema = coreschema.Object(properties=properties, required=required)
    return coreschema.render_to_form(schema)


@exclude_from_schema
def serve_docs(schema: APISchema, templates: Templates, path: Path) -> str:
    index = templates.get_template('apistar/docs/index.html')
    langs = ['python', 'javascript', 'shell']

    def static(path: str) -> str:
        return '/static/' + path

    def get_fields(link: Link, location: str) -> list:
        return [
            field for field in link.fields
            if field.location == location
        ]

    return index.render(
        document=schema,
        static=static,
        langs=langs,
        get_fields=get_fields,
        render_form=render_form,
        path=path
    )


docs_routes = [
    Route('/', 'GET', serve_docs),
    Route('/schema', 'GET', serve_schema),
    Route('/schema.js', 'GET', serve_schema_js),
]
