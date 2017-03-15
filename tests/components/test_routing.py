from apistar import App, Route
from apistar.components import http, test
from apistar.routing import URLArgs


def get_path(path: http.Path, args: URLArgs) -> http.Response:
    return http.Response({
        'path': path,
        'args': args
    })


app = App(routes=[
    Route('/path/<int:var>/', 'get', get_path),
])


client = test.RequestsClient(app)


def test_path():
    response = client.get('http://example.com/path/1/')
    assert response.json() == {
        'path': '/path/1/',
        'args': {'var': 1}
    }
