import inspect
import traceback
from collections import namedtuple
from typing import (  # noqa
    Any, Callable, Dict, Iterator, List, Sequence, Tuple, Union
)
from urllib.parse import urlparse

import werkzeug
from uritemplate import URITemplate
from werkzeug.routing import Map, Rule
from werkzeug.serving import is_running_from_reloader

from apistar import core, exceptions, http, schema, wsgi
from apistar.core import ArgName, Pipeline

primitive_types = (
    str, int, float, bool, list, dict
)

schema_types = (
    schema.String, schema.Integer, schema.Number, schema.Boolean,
    schema.Enum, schema.Object, schema.Array
)

typing_types = (
    List,
)


Route = namedtuple('Route', ['path', 'method', 'view'])
Include = namedtuple('Include', ['path', 'routes'])
Endpoint = namedtuple('Endpoint', ['view', 'pipeline'])
RoutesConfig = Sequence[Union[Route, Include]]


class Path(schema.String):
    format = 'path'


class URLPathArgs(dict):
    pass


class URLPathArg(object):
    schema = None  # type: type

    @classmethod
    def build(cls, args: URLPathArgs, arg_name: ArgName) -> Any:
        value = args.get(arg_name)
        if cls.schema is not None and not isinstance(value, cls.schema):
            try:
                value = cls.schema(value)
            except exceptions.SchemaError:
                raise exceptions.NotFound()
        return value


RouterLookup = Tuple[Callable, Pipeline, URLPathArgs]


class Router(object):
    def __init__(self,
                 routes: RoutesConfig,
                 initial_types: List[type]=None) -> None:
        required_type = wsgi.WSGIResponse

        initial_types = initial_types or []
        initial_types += [wsgi.WSGIEnviron, URLPathArgs, Exception]

        rules = []
        views = {}

        for (path, method, view) in walk(routes):
            view_signature = inspect.signature(view)
            uritemplate = URITemplate(path)

            # Ensure view arguments include all URL arguments
            for arg in uritemplate.variable_names:
                assert arg in view_signature.parameters, (
                    'URL argument "%s" in path "%s" must be included as a '
                    'keyword argument in the view function "%s"' %
                    (arg, path, view.__name__)
                )

            # Create a werkzeug path string
            werkzeug_path = path[:]
            for arg in uritemplate.variable_names:
                param = view_signature.parameters[arg]
                if param.annotation is inspect.Signature.empty:
                    converter = 'string'
                elif issubclass(param.annotation, (schema.String, str)):
                    if getattr(param.annotation, 'format', None) == 'path':
                        converter = 'path'
                    else:
                        converter = 'string'
                elif issubclass(param.annotation, (schema.Number, float)):
                    converter = 'float'
                elif issubclass(param.annotation, (schema.Integer, int)):
                    converter = 'int'
                else:
                    msg = 'Invalid type for path parameter, %s.' % param.annotation
                    raise exceptions.ConfigurationError(msg)

                werkzeug_path = werkzeug_path.replace(
                    '{%s}' % arg,
                    '<%s:%s>' % (converter, arg)
                )

            # Create a werkzeug routing rule
            name = view.__name__
            rule = Rule(werkzeug_path, methods=[method], endpoint=name)
            rules.append(rule)

            # Determine any inferred type annotations for the view
            extra_annotations = {}  # type: Dict[str, type]
            for param in view_signature.parameters.values():

                if param.annotation is inspect.Signature.empty:
                    annotated_type = str
                else:
                    annotated_type = param.annotation

                if param.name in uritemplate.variable_names:
                    class TypedURLPathArg(URLPathArg):
                        schema = annotated_type
                    extra_annotations[param.name] = TypedURLPathArg
                elif (annotated_type in primitive_types) or issubclass(annotated_type, schema_types):
                    if method in ('POST', 'PUT', 'PATCH'):
                        if issubclass(annotated_type, (schema.Object, schema.Array)):
                            class TypedDataParam(http.RequestData):
                                schema = annotated_type
                            extra_annotations[param.name] = TypedDataParam
                        else:
                            class TypedFieldParam(http.RequestField):
                                schema = annotated_type
                            extra_annotations[param.name] = TypedFieldParam
                    else:
                        class TypedQueryParam(http.QueryParam):
                            schema = annotated_type
                        extra_annotations[param.name] = TypedQueryParam

            return_annotation = view_signature.return_annotation
            if return_annotation is inspect.Signature.empty:
                extra_annotations['return'] = http.ResponseData
            elif issubclass(return_annotation, (schema_types, primitive_types, typing_types)):  # type: ignore
                extra_annotations['return'] = http.ResponseData

            # Determine the pipeline for the view.
            pipeline = core.build_pipeline(view, initial_types, required_type, extra_annotations)
            views[name] = Endpoint(view, pipeline)

        self.exception_pipeline = core.build_pipeline(exception_handler, initial_types, required_type, {})
        self.routes = routes
        self.adapter = Map(rules).bind('')
        self.views = views

    def lookup(self, path: str, method: str) -> RouterLookup:
        try:
            (name, kwargs) = self.adapter.match(path, method)
        except werkzeug.exceptions.NotFound:
            raise exceptions.NotFound()
        except werkzeug.exceptions.MethodNotAllowed:
            raise exceptions.MethodNotAllowed()
        except werkzeug.routing.RequestRedirect as exc:
            path = urlparse(exc.new_url).path
            raise exceptions.Found(path)

        (view, pipeline) = self.views[name]
        return (view, pipeline, kwargs)

    def reverse_url(self, view_name: str, **url_params: Dict[str, Any]) -> str:
        endpoint = self.views.get(view_name)
        if not endpoint:
            raise exceptions.NoReverseMatch

        flattened_routes = walk(self.routes)
        matched_views = [
            route for route in flattened_routes
            if route.view == endpoint.view
        ]

        return matched_views[0].path.format(**url_params)


def exception_handler(environ: wsgi.WSGIEnviron,
                      exc: Exception) -> http.Response:
    if isinstance(exc, exceptions.Found):
        return http.Response('', exc.status_code, {'Location': exc.location})

    if isinstance(exc, exceptions.APIException):
        if isinstance(exc.detail, str):
            content = {'message': exc.detail}
        else:
            content = exc.detail
        return http.Response(content, exc.status_code)

    if is_running_from_reloader() or environ.get('APISTAR_RAISE_500_EXC'):
        raise

    message = traceback.format_exc()
    return http.Response(message, 500, {'Content-Type': 'text/plain; charset=utf-8'})


def walk(routes: RoutesConfig, prefix: str='') -> Iterator[Route]:
    for entry in routes:
        if isinstance(entry, Include):
            yield from walk(entry.routes, prefix + entry.path)
        elif prefix:
            yield Route(prefix + entry.path, entry.method, entry.view)
        else:
            yield entry
