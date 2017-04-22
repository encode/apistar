import inspect
import traceback
from collections import namedtuple
from typing import Any, Callable, Dict, List, Tuple  # noqa

import werkzeug
from uritemplate import URITemplate
from werkzeug.routing import Map, Rule
from werkzeug.serving import is_running_from_reloader

from apistar import exceptions, http, pipelines, schema, wsgi
from apistar.pipelines import ArgName, Pipeline

# TODO: Path
# TODO: Redirects


primitive_types = (
    str, int, float, bool, list, dict
)

schema_types = (
    schema.String, schema.Integer, schema.Number, schema.Boolean
)

Route = namedtuple('Route', ['path', 'method', 'view'])
Endpoint = namedtuple('Endpoint', ['view', 'pipeline'])


class URLPathArgs(dict):
    pass


class URLPathArg(object):
    schema = None  # type: type

    @classmethod
    def build(cls, args: URLPathArgs, arg_name: ArgName):
        value = args.get(arg_name)
        if cls.schema is not None and not isinstance(value, cls.schema):
            try:
                value = cls.schema(value)
            except exceptions.SchemaError:
                raise exceptions.NotFound()
        return value


RouterLookup = Tuple[Callable, Pipeline, URLPathArgs]


class Router(object):
    def __init__(self, routes: List[Route], initial_types: List[type]=None) -> None:
        required_type = wsgi.WSGIResponse
        initial_types = initial_types or []
        initial_types += [wsgi.WSGIEnviron, URLPathArgs, Exception]

        rules = []
        views = {}

        for (path, method, view) in routes:
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

                if param.annotation == inspect.Signature.empty:
                    annotated_type = str
                else:
                    annotated_type = param.annotation

                if param.name in uritemplate.variable_names:
                    class TypedURLPathArg(URLPathArg):
                        schema = annotated_type
                    extra_annotations[param.name] = TypedURLPathArg
                elif (annotated_type in primitive_types) or issubclass(annotated_type, schema_types):
                    class TypedQueryParam(http.QueryParam):
                        schema = annotated_type
                    extra_annotations[param.name] = TypedQueryParam

            if 'return' not in view.__annotations__:
                extra_annotations['return'] = http.ResponseData

            # Determine the pipeline for the view.
            pipeline = pipelines.build_pipeline(view, initial_types, required_type, extra_annotations)
            views[name] = Endpoint(view, pipeline)

        self.exception_pipeline = pipelines.build_pipeline(exception_handler, initial_types, required_type, {})
        self.routes = routes
        self.adapter = Map(rules).bind('example.com')
        self.views = views

    def lookup(self, path, method) -> RouterLookup:
        try:
            (name, kwargs) = self.adapter.match(path, method)
        except werkzeug.exceptions.NotFound:
            raise exceptions.NotFound()
        except werkzeug.exceptions.MethodNotAllowed:
            raise exceptions.MethodNotAllowed()
        (view, pipeline) = self.views[name]
        return (view, pipeline, kwargs)


def exception_handler(environ: wsgi.WSGIEnviron, exc: Exception) -> http.Response:
    if isinstance(exc, exceptions.APIException):
        return http.Response({'message': exc.message}, exc.status_code)

    if is_running_from_reloader() or environ.get('APISTAR_RAISE_500_EXC'):
        raise

    message = traceback.format_exc()
    return http.Response(message, 500, {'Content-Type': 'text/plain; charset=utf-8'})
