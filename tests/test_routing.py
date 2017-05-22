import pytest

from apistar import App, Include, Route, exceptions, http, schema
from apistar.routing import Path, URLPathArgs
from apistar.test import TestClient


class MaxLength(schema.String):
    max_length = 5


def found():
    return {
        'message': 'Found'
    }


def path_params(args: URLPathArgs, var: int):
    return {
        'args': args
    }


def path_param(var):
    return {
        'var': var
    }


def path_param_with_int(var: int):
    return {
        'var': var
    }


def path_param_with_full_path(var: Path):
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


def subpath(var: schema.Integer):
    return {
        'var': var
    }


app = App(routes=[
    Route('/found/', 'GET', found),
    Route('/path_params/{var}/', 'GET', path_params),
    Route('/path_param/{var}/', 'GET', path_param),
    Route('/int/{var}/', 'GET', path_param_with_int),
    Route('/full_path/{var}', 'GET', path_param_with_full_path),
    Route('/max_length/{var}/', 'GET', path_param_with_max_length),
    Route('/number/{var}/', 'GET', path_param_with_number),
    Route('/integer/{var}/', 'GET', path_param_with_integer),
    Include('/subpath', [
        Route('/{var}/', 'GET', subpath),
    ]),
])


client = TestClient(app)


def test_200():
    response = client.get('/found/')
    assert response.status_code == 200
    assert response.json() == {
        'message': 'Found'
    }


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


def test_found_no_slash():
    response = client.get('/found', allow_redirects=False)
    assert response.status_code == 302
    assert response.headers['Location'] == '/found/'

    response = client.get('/found')
    assert response.status_code == 200
    assert response.url == 'http://testserver/found/'


def test_path_params():
    response = client.get('/path_params/1/')
    assert response.json() == {
        'args': {'var': 1}
    }


def test_path_param():
    response = client.get('/path_param/abc/')
    assert response.json() == {
        'var': 'abc'
    }


def test_int_path_param():
    response = client.get('/int/1/')
    assert response.json() == {
        'var': 1
    }


def test_subpath():
    response = client.get('/subpath/123/')
    assert response.json() == {
        'var': 123
    }


def test_full_path_param():
    response = client.get('/full_path/abc/def/ghi/')
    assert response.json() == {
        'var': 'abc/def/ghi/'
    }


def test_valid_max_length():
    response = client.get('/max_length/abcde/')
    assert response.status_code == 200
    assert response.json() == {
        'var': 'abcde'
    }


def test_invalid_max_length():
    response = client.get('/max_length/abcdef/')
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


def test_misconfigured_route():
    def set_type(var: set):  # pragma: nocover  (We never actually call this handler)
        pass

    with pytest.raises(exceptions.ConfigurationError):
        App(routes=[Route('/{var}/', 'GET', set_type)])


def test_lookup_cache_expiry():
    """
    Forcibly cycle the URL lookup cache, and ensure that
    we continue to generate correct lookups.
    """
    def get_path(var: int, path: http.Path):
        return {'path': path}

    routes = [
        Route('/{var}/', 'GET', get_path)
    ]
    settings = {'ROUTING': {'LOOKUP_CACHE_SIZE': 3}}
    app = App(routes=routes, settings=settings)
    client = TestClient(app)
    for index in range(10):
        response = client.get('/%d/' % index)
        assert response.status_code == 200
        assert response.json() == {'path': '/%d/' % index}


@pytest.mark.skip('WIP')
def test_routing_reversal_on_path_without_url_params():
    pass


@pytest.mark.skip('WIP')
def test_routing_reversal_on_path_non_existent_path():
    pass


@pytest.mark.skip('WIP')
def test_routing_reversal_on_path_with_url_params():
    pass


@pytest.mark.skip('WIP')
def test_routing_reversal_on_subpath_with_url_params():
    pass
