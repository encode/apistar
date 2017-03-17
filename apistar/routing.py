from apistar import pipelines
from apistar.components import http, wsgi
from collections import namedtuple
from typing import Any, List, TypeVar
from uritemplate import URITemplate
from werkzeug.routing import Map, Rule, parse_rule
import inspect
import json


Route = namedtuple('Route', ['path', 'method', 'view'])
Endpoint = namedtuple('Endpoint', ['view', 'pipeline'])


class URLArgs(dict):
    pass


NamedURLArg = TypeVar('NamedURLArg')
NamedURLArg.parent_type = URLArgs


class Router(object):
    converters = {
        str: 'string',
        int: 'int',
        float: 'float'
        # path, any, uuid
    }

    def __init__(self, routes: List[Route]) -> None:
        required_type = wsgi.WSGIResponse
        initial_types = [wsgi.WSGIEnviron, URLArgs]

        rules = []
        views = {}

        for (path, method, view) in routes:
            uritemplate = URITemplate(path)

            # Ensure view arguments include all URL arguments
            func_args = inspect.getfullargspec(view)[0]
            for arg in uritemplate.variable_names:
                assert arg in func_args, (
                    'URL argument "%s" in path "%s" must be included as a '
                    'keyword argument in the view function "%s"' %
                    (arg, path, view.__name__)
                )

            # Coerce any URL arguments to URLArg.
            werkzeug_path = path[:]
            arg_types = {}
            for arg in uritemplate.variable_names:
                arg_type = view.__annotations__.get(arg, str)
                converter = self.converters[arg_type]
                arg_types[arg] = arg_type
                werkzeug_path = werkzeug_path.replace(
                    '{%s}' % arg,
                    '<%s:%s>' % (converter, arg)
                )

            # Add any inferred type annotations to the view.
            extra_annotations = {}
            for arg in uritemplate.variable_names:
                extra_annotations[arg] = NamedURLArg
            if 'return' not in view.__annotations__:
                extra_annotations['return'] = http.ResponseData

            # Create a werkzeug routing rule.
            name = view.__name__
            rule = Rule(werkzeug_path, methods=[method], endpoint=name)
            rules.append(rule)

            # TODO: Apply type casting.

            # LATER: Ensure view arguments include all URL arguments
            # func_args = inspect.getfullargspec(view)[0]
            # assert arg in func_args, (
            #     'URL argument "%s" must be included in function "%s"' %
            #     (arg, view.__name__)
            # )

            # Determine the pipeline for the view.
            pipeline = pipelines.build_pipeline(view, initial_types, required_type, extra_annotations)
            views[name] = Endpoint(view, pipeline)

        self.adapter = Map(rules).bind('example.com')
        self.views = views

    def lookup(self, path, method):
        (name, kwargs) = self.adapter.match(path, method)
        (view, pipeline) = self.views[name]
        return (view, pipeline, kwargs)


def not_found_view() -> http.Response:
    return http.Response({'message': 'Not found'}, 404)
