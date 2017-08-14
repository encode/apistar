import inspect
import textwrap
import typing

import coreapi
import coreschema
import uritemplate

from apistar import exceptions, routing, typesystem
from apistar.interfaces import RouteConfig, Router, Schema

PRIMITIVE_TYPES = (
    str, int, float, bool, list, dict
)

SCHEMA_TYPES = (
    typesystem.String, typesystem.Integer, typesystem.Number, typesystem.Boolean,
    typesystem.Enum, typesystem.Object, typesystem.Array
)


class CoreAPISchema(Schema):
    def __init__(self, router: Router, routes: RouteConfig) -> None:
        try:
            url = router.reverse_url('serve_schema')
        except exceptions.NoReverseMatch:
            url = None

        content = {}
        for route in routing.flatten_routes(routes):
            if getattr(route.view, 'exclude_from_schema', False):
                continue
            content[route.name] = get_link(route)

        super().__init__(url=url, content=content)


def get_link(route: routing.Route) -> coreapi.Link:
    """
    Given a single route, return a Link instance containing all the information
    needed to expose that route in an API Schema.
    """
    path, method, view, name = route

    fields = []
    path_names = set(uritemplate.URITemplate(path).variable_names)
    for param in inspect.signature(view).parameters.values():
        field = get_field(param, method, path_names)
        if field is not None:
            fields.append(field)

    if view.__doc__:
        description = textwrap.dedent(view.__doc__).strip()
    else:
        description = None

    return coreapi.Link(url=path, action=method, description=description, fields=fields)


def get_field(param: inspect.Parameter,
              method: str,
              path_names: typing.Set[str]) -> typing.Optional[coreapi.Field]:
    if param.annotation is inspect.Signature.empty:
        annotated_type = str
    else:
        annotated_type = param.annotation

    if not inspect.isclass(annotated_type):
        return None  # Ignore type annotations

    if param.name in path_names:
        return coreapi.Field(
            name=param.name,
            location='path',
            required=True,
            schema=get_param_schema(annotated_type)
        )

    if issubclass(annotated_type, (dict, list)):
        return coreapi.Field(
            name=param.name,
            location='body',
            required=True,
            schema=get_param_schema(annotated_type)
        )

    return coreapi.Field(
        name=param.name,
        location='query',
        required=False,
        schema=get_param_schema(annotated_type)
    )


def get_param_schema(annotated_type: typing.Type) -> coreschema.schemas.Schema:
    if issubclass(annotated_type, (bool, typesystem.Boolean)):
        return coreschema.Boolean()
    elif issubclass(annotated_type, int):
        return coreschema.Integer()
    elif issubclass(annotated_type, float):
        return coreschema.Number()
    elif issubclass(annotated_type, typesystem.Enum):
        enum = typing.cast(typing.Type[typesystem.Enum], annotated_type)
        return coreschema.Enum(enum=enum.enum)
    return coreschema.String()
