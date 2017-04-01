from apistar import App, Route, http, schema
from apistar.routing import URLPathArgs
from apistar.test import TestClient


def found():
    return {
        'message': 'found'
    }


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
    Route('/found/', 'GET', found),
    Route('/args/{var}/', 'GET', get_args),
    Route('/arg/{var}/', 'GET', get_arg),
    Route('/query_param/', 'GET', get_query_param),
    Route('/query_param_with_schema/', 'GET', get_query_param_with_schema),
])


client = TestClient(app)


def test_404():
    response = client.get('http://example.com/404/')
    assert response.status_code == 404
    assert response.json() == {
        'message': 'Not found'
    }


def test_405():
    response = client.post('http://example.com/found/')
    assert response.status_code == 405
    assert response.json() == {
        'message': 'Method not allowed'
    }


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
