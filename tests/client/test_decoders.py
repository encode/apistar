import os

from starlette.applications import Starlette
from starlette.responses import PlainTextResponse, Response
from starlette.testclient import TestClient

from apistar.client import Client, decoders
from apistar.document import Document, Link

app = Starlette()


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


@app.route('/file-response-url-filename/name.png')
def file_response_url_filename(request):
    headers = {
        'Content-Type': 'image/png',
        'Content-Disposition': 'attachment'
    }
    return Response(b'<somedata>', headers=headers)


@app.route('/file-response-no-extension/name')
def file_response_no_extension(request):
    headers = {
        'Content-Type': 'image/png',
        'Content-Disposition': 'attachment'
    }
    return Response(b'<somedata>', headers=headers)


@app.route('/')
def file_response_no_name(request):
    headers = {
        'Content-Type': 'image/png',
        'Content-Disposition': 'attachment'
    }
    return Response(b'<somedata>', headers=headers)


document = Document(
    url='http://testserver',
    content=[
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
        Link(
            url='/file-response-url-filename/name.png',
            method='GET',
            name='file-response-url-filename',
        ),
        Link(
            url='/file-response-no-extension/name',
            method='GET',
            name='file-response-no-extension',
        ),
        Link(
            url='/',
            method='GET',
            name='file-response-no-name',
        ),
    ]
)


def test_text_response():
    client = Client(document, session=TestClient(app))
    data = client.request('text-response')
    assert data == 'hello, world'


def test_file_response():
    client = Client(document, session=TestClient(app))
    data = client.request('file-response')
    assert os.path.basename(data.name) == 'filename.png'
    assert data.read() == b'<somedata>'


def test_file_response_url_filename():
    client = Client(document, session=TestClient(app))
    data = client.request('file-response-url-filename')
    assert os.path.basename(data.name) == 'name.png'
    assert data.read() == b'<somedata>'


def test_file_response_no_extension():
    client = Client(document, session=TestClient(app))
    data = client.request('file-response-no-extension')
    assert os.path.basename(data.name) == 'name.png'
    assert data.read() == b'<somedata>'


def test_file_response_no_name():
    client = Client(document, session=TestClient(app))
    data = client.request('file-response-no-name')
    assert os.path.basename(data.name) == 'download.png'
    assert data.read() == b'<somedata>'


def test_unique_filename(tmpdir):
    client = Client(document, session=TestClient(app), decoders=[decoders.DownloadDecoder(tmpdir)])
    data = client.request('file-response')
    assert os.path.basename(data.name) == 'filename.png'
    assert data.read() == b'<somedata>'

    data = client.request('file-response')
    assert os.path.basename(data.name) == 'filename (1).png'
    assert data.read() == b'<somedata>'
