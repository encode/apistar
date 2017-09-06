import coreschema
from coreapi import Field, Link
from coreapi.codecs import CoreJSONCodec

from apistar import Route, Settings, TestClient, typesystem
from apistar.frameworks.wsgi import WSGIApp as App
from apistar.handlers import (
    api_documentation, javascript_schema, serve_schema, serve_static
)
from apistar.interfaces import Schema


class Category(typesystem.Enum):
    enum = ['shop', 'chore']


class ToDoNote(typesystem.Object):
    properties = {
        'id': typesystem.integer(minimum=0),
        'text': typesystem.string(max_length=100),
        'complete': typesystem.boolean(),
        'percent_complete': typesystem.number(),
        'category': Category
    }


def list_todo(search, settings: Settings):
    """
    list_todo description
    """
    raise NotImplementedError


def add_todo(note: ToDoNote):
    """
    add_todo description
    Multiple indented lines
    """
    raise NotImplementedError


def show_todo(ident: int):
    raise NotImplementedError


def set_percent_complete(ident: int, percent_complete: float):
    raise NotImplementedError


def set_complete(ident: int, complete: bool):
    raise NotImplementedError


def set_category(ident: int, category: Category):
    raise NotImplementedError


routes = [
    Route('/todo/', 'GET', list_todo),
    Route('/todo/', 'POST', add_todo),
    Route('/todo/{ident}/', 'GET', show_todo),
    Route('/todo/{ident}/', 'PUT', set_complete),
    Route('/todo/{ident}/percent_complete', 'PUT', set_percent_complete),
    Route('/todo/{ident}/category', 'PUT', set_category),
    Route('/docs/', 'GET', api_documentation),
    Route('/schema/', 'GET', serve_schema),
    Route('/schema.js', 'GET', javascript_schema),
    Route('/static/{path}', 'GET', serve_static)
]

app = App(routes=routes)

client = TestClient(app)

expected = Schema(url='/schema/', content={
    'list_todo': Link(
        url='/todo/',
        action='GET',
        description='list_todo description',
        fields=[Field(name='search', location='query', required=False, schema=coreschema.String())]
    ),
    'add_todo': Link(
        url='/todo/',
        action='POST',
        description='add_todo description\nMultiple indented lines',
        fields=[
            Field(name='id', required=False, location='form', schema=coreschema.Integer()),
            Field(name='text', required=False, location='form', schema=coreschema.String()),
            Field(name='complete', required=False, location='form', schema=coreschema.Boolean()),
            Field(name='percent_complete', required=False, location='form', schema=coreschema.Number()),
            Field(name='category', required=False, location='form', schema=coreschema.Enum(enum=['shop', 'chore']))
        ]
    ),
    'show_todo': Link(
        url='/todo/{ident}/',
        action='GET',
        fields=[Field(name='ident', location='path', required=True, schema=coreschema.Integer())]
    ),
    'set_complete': Link(
        url='/todo/{ident}/',
        action='PUT',
        fields=[
            Field(name='ident', location='path', required=True, schema=coreschema.Integer()),
            Field(name='complete', location='query', required=False, schema=coreschema.Boolean())
        ]
    ),
    'set_percent_complete': Link(
        url='/todo/{ident}/percent_complete',
        action='PUT',
        fields=[
            Field(name='ident', location='path', required=True, schema=coreschema.Integer()),
            Field(name='percent_complete', location='query', required=False, schema=coreschema.Number())
        ]
    ),
    'set_category': Link(
        url='/todo/{ident}/category',
        action='PUT',
        fields=[
            Field(name='ident', location='path', required=True, schema=coreschema.Integer()),
            Field(name='category', location='query', required=False, schema=coreschema.Enum(enum=['shop', 'chore']))
        ]
    )
})


def test_serve_schema():
    response = client.get('/schema/')
    codec = CoreJSONCodec()
    document = codec.decode(response.content)
    assert document.url == '/schema/'
    for name, link in expected.links.items():
        assert name in document
        assert link.action == document[name].action
        assert sorted(link.fields) == sorted(document[name].fields)


def test_javascript_schema():
    response = client.get('/schema.js')
    assert response.status_code == 200
    assert response.headers['Content-Type'] == 'application/javascript'


def test_api_documentation():
    response = client.get('/docs/')
    assert response.status_code == 200
    assert response.headers['Content-Type'] == 'text/html; charset=utf-8'
