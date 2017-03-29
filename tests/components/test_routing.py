from apistar import App, Route
from apistar.test import TestClient
from apistar.components import http
from apistar.routing import URLPathArgs


def get_args(path: http.Path, args: URLPathArgs, var: int):
    return {
        'path': path,
        'args': args
    }


def get_arg(path: http.Path, var: int):
    return {
        'path': path,
        'var': var
    }


app = App(routes=[
    Route('/args/{var}/', 'get', get_args),
    Route('/arg/{var}/', 'get', get_arg),
])


client = TestClient(app)


def test_args():
    response = client.get('http://example.com/args/1/')
    assert response.json() == {
        'path': '/args/1/',
        'args': {'var': 1}
    }


def test_arg():
    response = client.get('http://example.com/arg/1/')
    assert response.json() == {
        'path': '/arg/1/',
        'var': 1
    }
