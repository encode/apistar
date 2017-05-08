from coreapi import Field, Link
from coreapi.codecs import CoreJSONCodec

from apistar import schema
from apistar.apischema import APISchema, serve_schema
from apistar.app import App
from apistar.routing import Route
from apistar.test import TestClient


class ToDoNote(schema.Object):
    properties = {
        'id': schema.Integer(minimum=0),
        'text': schema.String(max_length=100),
        'complete': schema.Boolean
    }


def list_todo(app: App, search):  # pragma: nocover
    pass


def add_todo(note: ToDoNote):  # pragma: nocover
    pass


def show_todo(ident: int):  # pragma: nocover
    pass


def set_complete(ident: int, complete: bool):  # pragma: nocover
    pass


routes = [
    Route('/todo/', 'GET', list_todo),
    Route('/todo/', 'POST', add_todo),
    Route('/todo/{ident}/', 'GET', show_todo),
    Route('/todo/{ident}/', 'PUT', set_complete),
    Route('/schema/', 'GET', serve_schema)
]

app = App(routes=routes)

client = TestClient(app)

expected = APISchema(content={
    'list_todo': Link(
        url='/todo/',
        action='GET',
        fields=[Field(name='search', location='query', required=False)]
    ),
    'add_todo': Link(
        url='/todo/',
        action='POST',
        fields=[Field(name='note', location='body', required=True)]
    ),
    'show_todo': Link(
        url='/todo/{ident}/',
        action='GET',
        fields=[Field(name='ident', location='path', required=True)]
    ),
    'set_complete': Link(
        url='/todo/{ident}/',
        action='PUT',
        fields=[
            Field(name='ident', location='path', required=True),
            Field(name='complete', location='form', required=False)
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
    assert document == expected
