from apistar import pipelines, http, schema, wsgi
from apistar.pipelines import ArgName
from collections import namedtuple
from typing import Any, List, TypeVar
from uritemplate import URITemplate
from werkzeug.routing import Map, Rule, parse_rule
import inspect
import json
import werkzeug

# TODO: Path
# TODO: 404
# TODO: Redirects
# TODO: Caching


primitive_types = (
    str, int, float, bool, list, dict
)

schema_types = (
    schema.String, schema.Integer, schema.Number,
    schema.Boolean, schema.Object
)

Route = namedtuple('Route', ['path', 'method', 'view'])
Endpoint = namedtuple('Endpoint', ['view', 'pipeline'])


class URLPathArgs(dict):
    pass


class URLPathArg(object):
    schema = None

    @classmethod
    def build(cls, args: URLPathArgs, arg_name: ArgName):
        value = args.get(arg_name)
        if cls.schema is not None and not isinstance(value, cls.schema):
            value = cls.schema(value)
        return value


class Router(object):
    converters = {
        str: 'string',
        int: 'int',
        float: 'float',
        # path, any, uuid
    }
    not_found = None
    method_not_allowed = None

    def __init__(self, routes: List[Route]):
        from apistar.app import DBBackend
        required_type = wsgi.WSGIResponse
        initial_types = [DBBackend, wsgi.WSGIEnviron, URLPathArgs]

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
                if param.annotation == inspect.Signature.empty:
                    annotated_type = str
                else:
                    annotated_type = param.annotation
                converter = self.converters[annotated_type]
                werkzeug_path = werkzeug_path.replace(
                    '{%s}' % arg,
                    '<%s:%s>' % (converter, arg)
                )

            # Create a werkzeug routing rule
            name = view.__name__
            rule = Rule(werkzeug_path, methods=[method], endpoint=name)
            rules.append(rule)

            # Determine any inferred type annotations for the view
            extra_annotations = {}
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

        # Add pipelines for 404 and 405 cases.
        pipeline = pipelines.build_pipeline(view_404, initial_types, required_type, {})
        self.not_found = (None, pipeline, {})
        pipeline = pipelines.build_pipeline(view_405, initial_types, required_type, {})
        self.method_not_allowed = (None, pipeline, {})

        self.routes = routes
        self.adapter = Map(rules).bind('example.com')
        self.views = views

    def lookup(self, path, method):
        try:
            (name, kwargs) = self.adapter.match(path, method)
        except werkzeug.exceptions.NotFound:
            return self.not_found
        except werkzeug.exceptions.MethodNotAllowed:
            return self.method_not_allowed
        (view, pipeline) = self.views[name]
        return (view, pipeline, kwargs)


def view_404() -> http.Response:
    return http.Response({'message': 'Not found'}, 404)


def view_405() -> http.Response:
    return http.Response({'message': 'Method not allowed'}, 405)
