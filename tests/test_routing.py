from apistar import App, Route
from apistar import http, schema
from apistar.test import TestClient
from apistar.routing import URLPathArgs


def get_args(args: URLPathArgs, var: int):
    return {
        'args': args
    }


def get_arg(var: int):
    return {
        'var': var
    }


def get_query_param(query: float):
    return {
        'query': query
    }


def get_query_param_with_schema(query: schema.Number):
    return {
        'query': query
    }


app = App(routes=[
    Route('/args/{var}/', 'get', get_args),
    Route('/arg/{var}/', 'get', get_arg),
    Route('/query_param/', 'get', get_query_param),
    Route('/query_param_with_schema/', 'get', get_query_param_with_schema),
])


client = TestClient(app)


def test_args():
    response = client.get('http://example.com/args/1/')
    assert response.json() == {
        'args': {'var': 1}
    }


def test_arg():
    response = client.get('http://example.com/arg/1/')
    assert response.json() == {
        'var': 1
    }


def test_query_param():
    response = client.get('http://example.com/query_param/?query=1')
    assert response.json() == {
        'query': 1.0
    }


def test_query_param_with_schema():
    response = client.get('http://example.com/query_param_with_schema/?query=1')
    assert response.json() == {
        'query': 1.0
    }
