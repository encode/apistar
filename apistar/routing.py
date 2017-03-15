from apistar import pipelines
from apistar.components import http, wsgi
from collections import namedtuple
from typing import Any, List
from werkzeug.routing import Map, Rule, parse_rule
import inspect
import json


Route = namedtuple('Route', ['path', 'method', 'view'])
Endpoint = namedtuple('Endpoint', ['view', 'pipeline'])


class URLArgs(dict):
    pass


NamedURLArg = Any
NamedURLArg.parent_type = URLArgs


def parse_url_args(path):
    return [
        variable for converter, arguments, variable in parse_rule(path)
        if converter is not None
    ]


class Router(object):
    def __init__(self, routes: List[Route]):
        required_type = wsgi.WSGIResponse
        initial_types = [wsgi.WSGIEnviron, URLArgs]

        rules = []
        views = {}

        for (path, method, view) in routes:
            # Create a werkzeug routing rule.
            name = view.__name__
            rule = Rule(path, methods=[method], endpoint=name)
            rules.append(rule)

            # Coerce any URL arguments to URLArg.
            extra_annotations = {}
            args = parse_url_args(path)
            for arg in args:
                extra_annotations[arg] = NamedURLArg

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
