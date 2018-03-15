from apistar import App, Document, Field, Link, TestClient, http
from apistar.codecs import OpenAPICodec
from apistar.server.handlers import serve_schema


document = Document(
    title='API Star',
    content=[
        Link(url='/hello-world/', method='GET', name='hello_world', fields=[
            Field(name='username', location='query')
        ]),
        Link(url='/schema/', method='GET', handler=serve_schema),
    ]
)
app = App(document)
test_client = TestClient(app)


def test_get_schema():
    response = test_client.get('/schema/')
    assert response.status_code == 200
    codec = OpenAPICodec()
    document = codec.decode(response.content)
    assert document.title == 'API Star'
    assert len(document.get_links()) == 2
