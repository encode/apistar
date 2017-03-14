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
    required_type = wsgi.WSGIResponse
    initial_types = [wsgi.WSGIEnviron]

    for (path, method, view) in routes:
        pipeline = pipelines.build_pipeline(view, initial_types, required_type)
        mapping[(path, method.upper())] = Endpoint(view, pipeline)

    pipeline = pipelines.build_pipeline(not_found_view, initial_types, required_type)
    not_found = Endpoint(not_found_view, pipeline)

    def router(path, method):
        return mapping.get((path, method), not_found)

    return router
