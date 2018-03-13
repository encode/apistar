from apistar import http, App, Client, Document, Field, Link, Section, TestClient


def no_parameter():
    return http.Response({'hello': 'world'})


def query_parameter(params: http.QueryParams):
    return http.Response({'params': dict(params)})


# def path_parameters(params: http.QueryParams):
#     return http.Response({'params': dict(params)})


document = Document(
    url='http://testserver',
    content=[
        Link(url='/no-parameters/', method='GET', handler=no_parameter),
        Link(url='/query-parameter/', method='GET', handler=query_parameter, fields=[
            Field(name='a', location='query')
        ])
    ]
)
app = App(document)
session = TestClient(app)
client = Client(document=document, session=session)


def test_no_parameters():
    assert client.request('no_parameter') == {'hello': 'world'}

def test_query_parameter():
    assert client.request('query_parameter', a=1) == {'params': {'a': '1'}}
