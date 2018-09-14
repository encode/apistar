from apistar.client import Client
from apistar.document import Document, Field, Link
from starlette.applications import Starlette
from starlette.responses import JSONResponse, PlainTextResponse, Response
from starlette.testclient import TestClient
import os


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


@app.route('/text-response/')
def text_response(request):
    return PlainTextResponse('hello, world')


@app.route('/file-response/')
def file_response(request):
    headers = {
        'Content-Type': 'image/png',
        'Content-Disposition': 'attachment; filename="filename.png"'
    }
    return Response(b'<somedata>', headers=headers)


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
        ),
        Link(
            url='/text-response/',
            method='GET',
            name='text-response',
        ),
        Link(
            url='/file-response/',
            method='GET',
            name='file-response',
        ),
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


def test_text_response():
    client = Client(document, session=TestClient(app))
    data = client.request('text-response')
    assert data == 'hello, world'


def test_file_response():
    client = Client(document, session=TestClient(app))
    data = client.request('file-response')
    assert os.path.basename(data.name) == 'filename.png'
    assert data.read() == b'<somedata>'
