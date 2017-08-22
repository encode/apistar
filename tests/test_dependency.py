from typing import List, NewType

import pytest

from apistar import (
    Component, Route, TestClient, exceptions, http, types, typesystem
)
from apistar.frameworks.asyncio import ASyncIOApp
from apistar.frameworks.wsgi import WSGIApp


class KittenName(typesystem.String):
    max_length = 100


class KittenColor(typesystem.Enum):
    enum = [
        'black',
        'brown',
        'white',
        'grey',
        'tabby'
    ]


class Kitten(typesystem.Object):
    properties = {
        'name': KittenName,
        'color': KittenColor,
        'cuteness': typesystem.number(
            minimum=0.0,
            maximum=10.0,
            multiple_of=0.1
        )
    }


def list_favorite_kittens(color: KittenColor) -> List[Kitten]:
    """
    List your favorite kittens, optionally filtered by color.
    """
    kittens = [
        Kitten({'name': 'fluffums', 'color': 'white', 'cuteness': 9.8}),
        Kitten({'name': 'tabitha', 'color': 'tabby', 'cuteness': 8.7}),
        Kitten({'name': 'meowster', 'color': 'white', 'cuteness': 7.8}),
        Kitten({'name': 'fuzzball', 'color': 'brown', 'cuteness': 8.0}),
    ]
    return [
        kitten for kitten in kittens
        if kitten['color'] == color
    ]


def add_favorite_kitten(name: KittenName) -> Kitten:
    """
    Add a kitten to your favorites list.
    """
    return Kitten({'name': name, 'color': 'black', 'cuteness': 0.0})


routes = [
    Route('/list_favorite_kittens/', 'GET', list_favorite_kittens),
    Route('/add_favorite_kitten/', 'POST', add_favorite_kitten),
]

wsgi_app = WSGIApp(routes=routes)
async_app = ASyncIOApp(routes=routes)

wsgi_client = TestClient(wsgi_app)
async_client = TestClient(async_app)


@pytest.mark.parametrize('client', [wsgi_client, async_client])
def test_list_kittens(client):
    response = client.get('/list_favorite_kittens/?color=white')
    assert response.status_code == 200
    assert response.json() == [
        {'name': 'fluffums', 'color': 'white', 'cuteness': 9.8},
        {'name': 'meowster', 'color': 'white', 'cuteness': 7.8}
    ]


@pytest.mark.parametrize('client', [wsgi_client, async_client])
def test_add_kitten(client):
    response = client.post('/add_favorite_kitten/?name=charlie')
    assert response.status_code == 200
    assert response.json() == {
        'name': 'charlie', 'color': 'black', 'cuteness': 0.0
    }


@pytest.mark.parametrize('client', [wsgi_client, async_client])
def test_invalid_list_kittens(client):
    response = client.get('/list_favorite_kittens/?color=invalid')
    assert response.status_code == 400
    assert response.json() == {
        'color': 'Must be a valid choice.'
    }


@pytest.mark.parametrize('app_cls', [WSGIApp, ASyncIOApp])
def test_empty_arg_as_query_param(app_cls):
    def view(arg):
        return {'arg': arg}

    routes = [
        Route('/', 'GET', view)
    ]
    app = app_cls(routes=routes)
    client = TestClient(app)
    response = client.get('/?arg=123')
    assert response.json() == {
        'arg': '123'
    }


@pytest.mark.parametrize('app_cls', [WSGIApp, ASyncIOApp])
def test_cannot_coerce_query_param(app_cls):
    def view(arg: int):
        raise NotImplementedError

    routes = [
        Route('/', 'GET', view)
    ]
    app = app_cls(routes=routes)
    client = TestClient(app)
    response = client.get('/?arg=abc')
    assert response.status_code == 400
    assert response.json() == {
        'arg': "invalid literal for int() with base 10: 'abc'"
    }


@pytest.mark.parametrize('app_cls', [WSGIApp, ASyncIOApp])
def test_arg_as_composite_param(app_cls):
    def view(arg: dict):
        return {'arg': arg}

    routes = [
        Route('/', 'POST', view)
    ]
    app = app_cls(routes=routes)
    client = TestClient(app)
    response = client.post('/', json={'a': 123})
    assert response.json() == {
        'arg': {'a': 123}
    }


@pytest.mark.parametrize('app_cls', [WSGIApp, ASyncIOApp])
def test_cannot_coerce_body_param(app_cls):
    def view(arg: dict):
        raise NotImplementedError

    routes = [
        Route('/', 'POST', view)
    ]
    app = app_cls(routes=routes)
    client = TestClient(app)
    response = client.post('/', json=123)
    assert response.status_code == 400
    assert response.json() == {
        'message': "'int' object is not iterable"
    }


@pytest.mark.parametrize('app_cls', [WSGIApp, ASyncIOApp])
def test_cannot_inject_unkown_component(app_cls):
    class A():
        pass

    def view(component: A):
        raise NotImplementedError

    routes = [
        Route('/', 'GET', view)
    ]
    app = app_cls(routes=routes)
    client = TestClient(app)
    with pytest.raises(exceptions.CouldNotResolveDependency):
        client.get('/')


@pytest.mark.parametrize('app_cls', [WSGIApp, ASyncIOApp])
def test_component_injected_twice_runs_once(app_cls):
    log = []

    class LoggingComponent():
        def __init__(self, method: http.Method, path: http.Path) -> None:
            nonlocal log
            log.append('logging component injected')

    def view(a: LoggingComponent, b: LoggingComponent):
        return

    routes = [
        Route('/', 'GET', view)
    ]
    components = [
        Component(LoggingComponent)
    ]
    app = app_cls(routes=routes, components=components)
    client = TestClient(app)
    client.get('/')
    assert log == ['logging component injected']


@pytest.mark.parametrize('app_cls', [WSGIApp, ASyncIOApp])
def test_context_manager_component(app_cls):
    log = []

    class ContextManagerComponent():
        def __init__(self, method: http.Method, path: http.Path) -> None:
            pass

        def __enter__(self):
            nonlocal log
            log.append('context manager enter')

        def __exit__(self, *args, **kwargs):
            nonlocal log
            log.append('context manager exit')

    def view(c: ContextManagerComponent):
        nonlocal log
        log.append('view')
        return

    routes = [
        Route('/', 'GET', view)
    ]
    components = [
        Component(ContextManagerComponent)
    ]
    app = app_cls(routes=routes, components=components)
    client = TestClient(app)
    client.get('/')
    assert log == ['context manager enter', 'view', 'context manager exit']


@pytest.mark.parametrize('app_cls', [WSGIApp, ASyncIOApp])
def test_param_name_component(app_cls):
    """
    Test for issue #246 (allow ParamName to be used in top-level component)
    https://github.com/encode/apistar/issues/246
    """

    def get_value(name: types.ParamName):
        values = {'foo': 'bar'}
        return values[name]

    GetValue = NewType('GetValue', str)

    def print_value(foo: GetValue):
        return foo

    app = app_cls(
        routes=[Route('/', 'GET', print_value)],
        components=[Component(GetValue, init=get_value)])
    client = TestClient(app)

    assert client.get('/').content == b'bar'
