from apistar import pipelines
from apistar.components import http, wsgi
from collections import namedtuple
import json


Route = namedtuple('Route', ['path', 'method', 'view'])
Endpoint = namedtuple('Endpoint', ['view', 'pipeline'])


def not_found_view() -> http.Response:
    return http.Response({'message': 'Not found'}, 404)


def get_router(routes):
    mapping = {}
    requirement = wsgi.WSGIResponse
    initial_types = [wsgi.WSGIEnviron]

    for (path, method, view) in routes:
        functions = [view] + [wsgi.WSGIResponse.build]
        pipeline, seen_types = pipelines.build_function_pipeline(functions, initial_types)
        mapping[(path, method.upper())] = Endpoint(view, pipeline)

    functions = [not_found_view] + [wsgi.WSGIResponse.build]
    pipeline, seen_types = pipelines.build_function_pipeline(functions, initial_types)
    not_found = Endpoint(not_found_view, pipeline)

    def router(path, method):
        return mapping.get((path, method), not_found)

    return router
