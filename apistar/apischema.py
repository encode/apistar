import inspect
from typing import Dict, List

from coreapi import Document, Field, Link
from coreapi.codecs import CoreJSONCodec
from uritemplate import URITemplate

from apistar import http, schema
from apistar.app import App
from apistar.decorators import exclude_from_schema
from apistar.routing import Route, primitive_types, schema_types


class APISchema(Document):
    @classmethod
    def build(cls, app: App):
        content = get_content(app.routes)
        return cls(content=content)


def get_content(routes: List[Route]) -> Dict[str, Route]:
    """
    Given the application routes, return a dictionary containing all the
    Links that the service exposes.
    """
    content = {}
    for route in routes:
        view = route.view
        if getattr(view, 'exclude_from_schema', False):
            continue
        name = view.__name__
        link = get_link(route)
        content[name] = link
    return content


def get_link(route: Route) -> Link:
    """
    Given a single route, return a Link instance containing all the information
    needed to expose that route in an API Schema.
    """
    path, method, view = route

    view_signature = inspect.signature(view)
    uritemplate = URITemplate(path)

    fields = []
    for param in view_signature.parameters.values():

        if param.annotation is inspect.Signature.empty:
            annotated_type = str
        else:
            annotated_type = param.annotation

        location = None
        required = False
        if param.name in uritemplate.variable_names:
            location = 'path'
            required = True
        elif (annotated_type in primitive_types) or issubclass(annotated_type, schema_types):
            if method in ('POST', 'PUT', 'PATCH'):
                if issubclass(annotated_type, schema.Object):
                    location = 'body'
                    required = True
                else:
                    location = 'form'
            else:
                location = 'query'

        if location is not None:
            field = Field(name=param.name, location=location, required=required)
            fields.append(field)

    return Link(url=path, action=method, fields=fields)


@exclude_from_schema
def serve_schema(schema: APISchema) -> http.Response:
    codec = CoreJSONCodec()
    content = codec.encode(schema)
    headers = {'Content-Type': codec.media_type}
    return http.Response(content, headers=headers)
