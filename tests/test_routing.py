from apistar import App, Route, schema
from apistar.routing import URLPathArgs
from apistar.test import TestClient


class MaxLength(schema.String):
    max_length = 10


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


def path_param_with_max_length(var: MaxLength):
    return {
        'var': var
    }


def path_param_with_number(var: schema.Number):
    return {
        'var': var
    }


def path_param_with_integer(var: schema.Integer):
    return {
        'var': var
    }


app = App(routes=[
    Route('/found/', 'GET', found),
    Route('/args/{var}/', 'GET', get_args),
    Route('/arg/{var}/', 'GET', get_arg),
    Route('/max_length/{var}/', 'GET', path_param_with_max_length),
    Route('/number/{var}/', 'GET', path_param_with_number),
    Route('/integer/{var}/', 'GET', path_param_with_integer),
])


client = TestClient(app)


def test_404():
    response = client.get('/404/')
    assert response.status_code == 404
    assert response.json() == {
        'message': 'Not found'
    }


def test_405():
    response = client.post('/found/')
    assert response.status_code == 405
    assert response.json() == {
        'message': 'Method not allowed'
    }


def test_args():
    response = client.get('/args/1/')
    assert response.json() == {
        'args': {'var': 1}
    }


def test_arg():
    response = client.get('/arg/1/')
    assert response.json() == {
        'var': 1
    }


def test_valid_max_length():
    response = client.get('/max_length/abcde/')
    assert response.status_code == 200
    assert response.json() == {
        'var': 'abcde'
    }


def test_invalid_max_length():
    response = client.get('/arg/abcdef/')
    assert response.status_code == 404
    assert response.json() == {
        'message': 'Not found'
    }


def test_valid_number():
    response = client.get('/number/1.23/')
    assert response.status_code == 200
    assert response.json() == {
        'var': 1.23
    }


def test_invalid_number():
    response = client.get('/number/abc/')
    assert response.status_code == 404
    assert response.json() == {
        'message': 'Not found'
    }


def test_valid_integer():
    response = client.get('/integer/123/')
    assert response.status_code == 200
    assert response.json() == {
        'var': 123
    }


def test_invalid_integer():
    response = client.get('/integer/abc/')
    assert response.status_code == 404
    assert response.json() == {
        'message': 'Not found'
    }
