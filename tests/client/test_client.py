from starlette.applications import Starlette
from starlette.responses import JSONResponse
from starlette.testclient import TestClient

from apistar.client import Client
from apistar.document import Document, Field, Link

app = Starlette()


@app.route('/path-param/{value}')
def path_param(request, value):
    return JSONResponse({'value': value})


@app.route('/query-params/')
def query_params(request):
    return JSONResponse({'query': dict(request.query_params)})


@app.route('/body-param/', methods=['POST'])
async def body_param(request):
    data = await request.json()
    return JSONResponse({'body': dict(data)})


document = Document(
    url='http://testserver',
    content=[
        Link(
            url='/path-param/{value}',
            method='GET',
            name='path-param',
            fields=[
                Field(name='value', location='path')
            ]
        ),
        Link(
            url='/query-params/',
            method='GET',
            name='query-params',
            fields=[
                Field(name='a', location='query'),
                Field(name='b', location='query'),
            ]
        ),
        Link(
            url='/body-param/',
            method='POST',
            name='body-param',
            encoding='application/json',
            fields=[
                Field(name='value', location='body')
            ]
        )
    ]
)


def test_path_param():
    client = Client(document, session=TestClient(app))
    data = client.request('path-param', value=123)
    assert data == {'value': '123'}


def test_query_params():
    client = Client(document, session=TestClient(app))
    data = client.request('query-params', a=123, b=456)
    assert data == {'query': {'a': '123', 'b': '456'}}


def test_body_param():
    client = Client(document, session=TestClient(app))
    data = client.request('body-param', value={'example': 123})
    assert data == {'body': {'example': 123}}
