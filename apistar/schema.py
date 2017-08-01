import inspect
import textwrap
import typing

import coreapi
import coreschema
import uritemplate

from apistar import typesystem
from apistar.interfaces import Route, Router

PRIMITIVE_TYPES = (
    str, int, float, bool, list, dict
)

SCHEMA_TYPES = (
    typesystem.String, typesystem.Integer, typesystem.Number, typesystem.Boolean,
    typesystem.Enum, typesystem.Object, typesystem.Array
)


def get_schema(router: Router) -> coreapi.Document:
    routes = router.get_routes()
    content = get_schema_content(routes)
    return coreapi.Document(url='/', content=content)


def get_schema_content(routes: typing.Sequence[Route]) -> typing.Dict[str, coreapi.Link]:
    """
    Given the application routes, return a dictionary containing all the
    Links that the service exposes.
    """
    content = {}
    for route in routes:
        if getattr(route.view, 'exclude_from_schema', False):
            continue
        content[route.view.__name__] = get_link(route)
    return content


def get_link(route: Route) -> coreapi.Link:
    """
    Given a single route, return a Link instance containing all the information
    needed to expose that route in an API Schema.
    """
    path, method, view = route

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
        return None

    if param.name in path_names:
        return coreapi.Field(
            name=param.name,
            location='path',
            required=True,
            schema=get_param_schema(annotated_type)
        )
    elif (annotated_type in PRIMITIVE_TYPES) or issubclass(annotated_type, SCHEMA_TYPES):
        if method in ('POST', 'PUT', 'PATCH'):
            if issubclass(annotated_type, typesystem.Object):
                return coreapi.Field(
                    name=param.name,
                    location='body',
                    required=True,
                    schema=get_param_schema(annotated_type)
                )
            else:
                return coreapi.Field(
                    name=param.name,
                    location='form',
                    required=False,
                    schema=get_param_schema(annotated_type)
                )
        else:
            return coreapi.Field(
                name=param.name,
                location='query',
                required=False,
                schema=get_param_schema(annotated_type)
            )
    return None


def get_param_schema(annotated_type: typing.Type) -> coreschema.schemas.Schema:
    if annotated_type is bool or issubclass(annotated_type, typesystem.Boolean):
        return coreschema.Boolean()
    elif annotated_type is int or issubclass(annotated_type, typesystem.Integer):
        return coreschema.Integer()
    elif annotated_type is float or issubclass(annotated_type, typesystem.Number):
        return coreschema.Number()
    elif issubclass(annotated_type, typesystem.Enum):
        enum = typing.cast(typing.Type[typesystem.Enum], annotated_type)
        return coreschema.Enum(enum=enum.enum)
    return coreschema.String()
