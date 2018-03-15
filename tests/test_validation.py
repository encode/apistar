from apistar import types
from apistar.document import Document, Field, Link
from apistar.server import http
from apistar.server.app import App
from apistar.server.test import TestClient


def str_path_param(param: str) -> http.Response:
    return http.Response({'param': param})


def int_path_param(param: int) -> http.Response:
    return http.Response({'param': param})


def str_query_param(param: str) -> http.Response:
    return http.Response({'param': param})


def int_query_param(param: int) -> http.Response:
    return http.Response({'param': param})


def schema_enforced_str_path_param(param) -> http.Response:
    return http.Response({'param': param})


def schema_enforced_int_path_param(param) -> http.Response:
    return http.Response({'param': param})


def schema_enforced_str_query_param(param) -> http.Response:
    return http.Response({'param': param})


def schema_enforced_int_query_param(param) -> http.Response:
    return http.Response({'param': param})


doc = Document([
    Link(url='/str_path_param/{param}/', method='GET', handler=str_path_param),
    Link(url='/int_path_param/{param}/', method='GET', handler=int_path_param),
    Link(
        url='/schema_enforced_str_path_param/{param}/',
        method='GET',
        handler=schema_enforced_str_path_param,
        fields=[
            Field(name='param', location='path', required=True, schema=types.String(max_length=3))
        ]
    ),
    Link(
        url='/schema_enforced_int_path_param/{param}/',
        method='GET',
        handler=schema_enforced_int_path_param,
        fields=[
            Field(name='param', location='path', required=True, schema=types.Integer(minimum=0, maximum=1000))
        ]
    ),
    Link(url='/str_query_param/', method='GET', handler=str_query_param),
    Link(url='/int_query_param/', method='GET', handler=int_query_param),
    Link(
        url='/schema_enforced_str_query_param/',
        method='GET',
        handler=schema_enforced_str_query_param,
        fields=[
            Field(name='param', location='query', schema=types.String(max_length=3))
        ]
    ),
    Link(
        url='/schema_enforced_int_query_param/',
        method='GET',
        handler=schema_enforced_int_query_param,
        fields=[
            Field(name='param', location='query', schema=types.Integer(minimum=0, maximum=1000))
        ]
    ),
])

app = App(doc)
client = TestClient(app)


def test_str_path_param():
    response = client.get('/str_path_param/123/')
    assert response.json() == {'param': '123'}


def test_schema_enforced_str_path_param():
    response = client.get('/schema_enforced_str_path_param/123/')
    assert response.json() == {'param': '123'}
    response = client.get('/schema_enforced_str_path_param/1234/')
    assert response.status_code == 404
    assert response.json() == {'param': 'Must have no more than 3 characters.'}


def test_int_path_param():
    response = client.get('/int_path_param/123/')
    assert response.json() == {'param': 123}


def test_schema_enforced_int_path_param():
    response = client.get('/schema_enforced_int_path_param/123/')
    assert response.json() == {'param': 123}
    response = client.get('/schema_enforced_int_path_param/1234/')
    assert response.status_code == 404
    assert response.json() == {'param': 'Must be less than or equal to 1000.'}


def test_str_query_param():
    response = client.get('/str_query_param/?param=123')
    assert response.json() == {'param': '123'}


def test_schema_enforced_str_query_param():
    response = client.get('/schema_enforced_str_query_param/?param=123')
    assert response.json() == {'param': '123'}
    response = client.get('/schema_enforced_str_query_param/?param=1234')
    assert response.status_code == 400
    assert response.json() == {'param': 'Must have no more than 3 characters.'}


def test_int_query_param():
    response = client.get('/int_query_param/?param=123')
    assert response.json() == {'param': 123}


def test_schema_enforced_int_query_param():
    response = client.get('/schema_enforced_int_query_param/?param=123')
    assert response.json() == {'param': 123}
    response = client.get('/schema_enforced_int_query_param/?param=1234')
    assert response.status_code == 400
    assert response.json() == {'param': 'Must be less than or equal to 1000.'}
