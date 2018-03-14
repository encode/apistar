from apistar import App, Document, Link, TestClient, http
from apistar.codecs import OpenAPICodec
from apistar.server.handlers import serve_schema


def hello_world():
    return http.Response({'hello': 'world'})


document = Document(
    title='API Star',
    content=[
        Link(url='/hello-world/', method='GET', handler=hello_world),
        Link(url='/schema/', method='GET', handler=serve_schema),
    ]
)
app = App(document)
client = TestClient(app)


def test_get_schema():
    response = client.get('/schema/')
    assert response.status_code == 200
    codec = OpenAPICodec()
    document = codec.decode(response.content)
    assert document.title == 'API Star'
    assert len(document.get_links()) == 2
