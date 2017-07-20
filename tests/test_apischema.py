import coreschema
from coreapi import Field, Link
from coreapi.codecs import CoreJSONCodec

from apistar import schema
from apistar.apischema import APISchema, serve_schema, serve_schema_js
from apistar.app import App
from apistar.docs import serve_docs
from apistar.routing import Route
from apistar.test import TestClient


class Category(schema.Enum):
    enum = ['shop', 'chore']


class ToDoNote(schema.Object):
    properties = {
        'id': schema.Integer(minimum=0),
        'text': schema.String(max_length=100),
        'complete': schema.Boolean,
        'percent_complete': schema.Number,
        'category': Category
    }


def list_todo(app: App, search):  # pragma: nocover
    """
    list_todo description
    """
    pass


def add_todo(note: ToDoNote):  # pragma: nocover
    """
    add_todo description
    Multiple indented lines
    """
    pass


def show_todo(ident: int):  # pragma: nocover
    pass


def set_percent_complete(ident: int, percent_complete: float):  # pragma: nocover
    pass


def set_complete(ident: int, complete: bool):  # pragma: nocover
    pass


def set_category(ident: int, category: Category):  # pragma: nocover
    pass


routes = [
    Route('/todo/', 'GET', list_todo),
    Route('/todo/', 'POST', add_todo),
    Route('/todo/{ident}/', 'GET', show_todo),
    Route('/todo/{ident}/', 'PUT', set_complete),
    Route('/todo/{ident}/percent_complete', 'PUT', set_percent_complete),
    Route('/todo/{ident}/category', 'PUT', set_category),
    Route('/schema/', 'GET', serve_schema),
    Route('/docs/', 'GET', serve_docs),
    Route('/schema.js', 'GET', serve_schema_js)
]

app = App(routes=routes)

client = TestClient(app)

expected = APISchema(url='/schema/', content={
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
        fields=[Field(name='note', location='body', required=True, schema=coreschema.String())]
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
            Field(name='complete', location='form', required=False, schema=coreschema.Boolean())
        ]
    ),
    'set_percent_complete': Link(
        url='/todo/{ident}/percent_complete',
        action='PUT',
        fields=[
            Field(name='ident', location='path', required=True, schema=coreschema.Integer()),
            Field(name='percent_complete', location='form', required=False, schema=coreschema.Number())
        ]
    ),
    'set_category': Link(
        url='/todo/{ident}/category',
        action='PUT',
        fields=[
            Field(name='ident', location='path', required=True, schema=coreschema.Integer()),
            Field(name='category', location='form', required=False, schema=coreschema.Enum(enum=['shop', 'chore']))
        ]
    )
})


def test_api_schema():
    schema = APISchema.build(app)
    assert schema == expected


def test_serve_schema():
    response = client.get('/schema/')
    codec = CoreJSONCodec()
    document = codec.decode(response.content)
    assert document.url == 'http://testserver/schema/'
    for name, link in expected.links.items():
        assert name in document
        assert link.action == document[name].action
        assert link.fields == document[name].fields


def test_serve_schema_js():
    response = client.get('/schema.js')
    assert response.status_code == 200
    assert response.headers['Content-Type'] == 'application/javascript'


def test_serve_docs():
    response = client.get('/docs/')
    assert response.status_code == 200
    assert response.headers['Content-Type'] == 'text/html; charset=utf-8'
