import inspect
import textwrap
import typing

import coreapi
import coreschema
import uritemplate

from apistar import Route, Settings, exceptions, typesystem
from apistar.core import flatten_routes
from apistar.interfaces import Router, Schema
from apistar.types import RouteConfig

SCHEMA_SCALAR_TYPES = (
    typesystem.String, typesystem.Integer, typesystem.Number,
    typesystem.Boolean, typesystem.Enum
)

SCHEMA_CONTAINER_TYPES = (
    typesystem.Object, typesystem.Array
)

PRIMITIVE_TYPES_TO_SCHEMA_TYPES = {
    dict: typesystem.Object,
    list: typesystem.Array,
    int: typesystem.Integer,
    float: typesystem.Number,
    str: typesystem.String,
    bool: typesystem.Boolean
}


def annotation_to_type(annotation):
    if annotation is inspect.Signature.empty:
        return typesystem.String
    return PRIMITIVE_TYPES_TO_SCHEMA_TYPES.get(annotation, annotation)


class CoreAPISchema(Schema):
    def __init__(self, router: Router, routes: RouteConfig, settings: Settings) -> None:
        try:
            url = router.reverse_url('serve_schema')
        except exceptions.NoReverseMatch:
            url = None

        content = {}
        for route in flatten_routes(routes):
            if getattr(route.view, 'exclude_from_schema', False):
                continue
            content[route.name] = get_link(route)

        schema_settings = settings.get('SCHEMA', {})
        title = schema_settings.get('TITLE', '')
        description = schema_settings.get('DESCRIPTION', '')
        url = schema_settings.get('URL', url)

        super().__init__(title=title, description=description, url=url, content=content)


def get_link(route: Route) -> coreapi.Link:
    """
    Given a single route, return a Link instance containing all the information
    needed to expose that route in an API Schema.
    """
    path, method, view, name = route

    fields = []  # type: typing.List[coreapi.Field]
    path_names = set(uritemplate.URITemplate(path).variable_names)
    for param in inspect.signature(view).parameters.values():
        fields += get_fields(param, method, path_names)

    if view.__doc__:
        description = textwrap.dedent(view.__doc__).strip()
    else:
        description = None

    return coreapi.Link(url=path, action=method, description=description, fields=fields)


def get_fields(param: inspect.Parameter,
               method: str,
               path_names: typing.Set[str]) -> typing.Optional[coreapi.Field]:
    field_type = annotation_to_type(param.annotation)

    if not inspect.isclass(field_type):
        return []  # Ignore type annotations

    if param.name in path_names:
        return [coreapi.Field(
            name=param.name,
            location='path',
            required=True,
            schema=get_param_schema(field_type)
        )]

    elif issubclass(field_type, typesystem.Object):
        return [
            coreapi.Field(
                name=name,
                location='form',
                required=False,
                schema=get_param_schema(value)
            )
            for name, value in field_type.properties.items()
        ]

    elif issubclass(field_type, typesystem.Array):
        return [coreapi.Field(
            name=param.name,
            location='body',
            required=True,
            schema=get_param_schema(field_type)
        )]

    elif issubclass(field_type, SCHEMA_SCALAR_TYPES):
        return [coreapi.Field(
            name=param.name,
            location='query',
            required=False,
            schema=get_param_schema(field_type)
        )]

    return []


def get_param_schema(annotated_type: typing.Type) -> coreschema.schemas.Schema:
    schema_kwargs = {
        'description': getattr(annotated_type, 'description', '')
    }

    if issubclass(annotated_type, (bool, typesystem.Boolean)):
        return coreschema.Boolean(**schema_kwargs)
    elif issubclass(annotated_type, int):
        return coreschema.Integer(**schema_kwargs)
    elif issubclass(annotated_type, float):
        return coreschema.Number(**schema_kwargs)
    elif issubclass(annotated_type, typesystem.Enum):
        enum = typing.cast(typing.Type[typesystem.Enum], annotated_type)
        return coreschema.Enum(enum=enum.enum, **schema_kwargs)
    return coreschema.String(**schema_kwargs)
