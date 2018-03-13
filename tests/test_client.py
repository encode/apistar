from apistar import App, Client, Document, Field, Link, Section, TestClient, exceptions, http
import pytest


def no_parameter():
    return http.Response({'hello': 'world'})


def query_parameter(params: http.QueryParams):
    return http.Response({'params': dict(params)})


def text_response():
    return http.Response('Hello, world!', headers={'Content-Type': 'text/plain'})


def empty_response():
    return http.Response(status=204)


def error_response():
    return http.Response({'error': 'failed'}, status=400)


document = Document(
    url='http://testserver',
    content=[
        Section(name='parameters', content=[
            Link(url='/no-parameters/', method='GET', handler=no_parameter),
            Link(url='/query-parameter/', method='GET', handler=query_parameter, fields=[
                Field(name='a', location='query')
            ])
        ]),
        Section(name='responses', content=[
            Link(url='/text-response/', method='GET', handler=text_response),
            Link(url='/empty-response/', method='GET', handler=empty_response),
            Link(url='/error-response/', method='GET', handler=error_response)
        ]),
    ]
)
app = App(document)
session = TestClient(app)
client = Client(document=document, session=session)


def test_no_parameters():
    assert client.request('parameters:no_parameter') == {'hello': 'world'}

def test_query_parameter():
    assert client.request('parameters:query_parameter', a=1) == {'params': {'a': '1'}}

def test_text_response():
    assert client.request('responses:text_response') == 'Hello, world!'

def test_empty_response():
    assert client.request('responses:empty_response') is None

def test_error_response():
    with pytest.raises(exceptions.ErrorResponse) as exc:
        client.request('responses:error_response')
    assert exc.value.title == '400 Bad Request'
    assert exc.value.content == {'error': 'failed'}
