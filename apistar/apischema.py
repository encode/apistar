import base64
import inspect
from typing import Dict, Optional, cast
if False:
    from typing import Type
from urllib.parse import urljoin

import coreschema
from coreapi import Document, Field, Link
from coreapi.codecs import CoreJSONCodec
from uritemplate import URITemplate

from apistar import http, schema
from apistar.app import App
from apistar.decorators import exclude_from_schema
from apistar.routing import (
    Route, RoutesConfig, primitive_types, schema_types, walk
)
from apistar.templating import Templates


class APISchema(Document):
    @classmethod
    def build(cls, app: App, base_url: http.URL=None):
        routes = app.routes
        url = get_schema_url(routes, base_url)
        content = get_schema_content(routes)
        return cls(url=url, content=content)


def get_schema_url(routes: RoutesConfig, base_url: http.URL=None) -> Optional[str]:
    """
    Given the application routes, return the URL path of the API Schema.
    """
    for route in walk(routes):
        if route.view is serve_schema:
            return urljoin(base_url, route.path)
    return None  # pragma: nocover


def get_schema_content(routes: RoutesConfig) -> Dict[str, Route]:
    """
    Given the application routes, return a dictionary containing all the
    Links that the service exposes.
    """
    content = {}
    for route in walk(routes):
        view = route.view
        if getattr(view, 'exclude_from_schema', False):
            continue
        name = view.__name__
        link = get_link(route)
        content[name] = link
    return content


def _annotated_type_to_coreschema(annotated_type: type) -> coreschema.schemas.Schema:
    if annotated_type is bool or issubclass(annotated_type, schema.Boolean):
        return coreschema.Boolean()
    elif annotated_type is int or issubclass(annotated_type, schema.Integer):
        return coreschema.Integer()
    elif annotated_type is float or issubclass(annotated_type, schema.Number):
        return coreschema.Number()
    elif issubclass(annotated_type, schema.Enum):
        enum = cast(Type[schema.Enum], annotated_type)
        return coreschema.Enum(enum=enum.enum)

    return coreschema.String()


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
        param_schema = _annotated_type_to_coreschema(annotated_type)
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
            field = Field(name=param.name, location=location, required=required, schema=param_schema)
            fields.append(field)

    return Link(url=path, action=method, fields=fields)


@exclude_from_schema
def serve_schema(schema: APISchema) -> http.Response:
    codec = CoreJSONCodec()
    content = codec.encode(schema)
    headers = {'Content-Type': codec.media_type}
    return http.Response(content, headers=headers)


@exclude_from_schema
def serve_schema_js(schema: APISchema, templates: Templates) -> http.Response:
    codec = CoreJSONCodec()
    base64_schema = base64.b64encode(codec.encode(schema)).decode('latin1')
    template = templates.get_template('apistar/schema.js')
    content = template.render(base64_schema=base64_schema)
    headers = {'Content-Type': 'application/javascript'}
    return http.Response(content, headers=headers)
