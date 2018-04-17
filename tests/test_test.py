from apistar import App, Route, TestClient, types, validators
from apistar.server.handlers import serve_schema


class WSGIMiddleware:

    def __init__(self, app):
        self.app = app

    def __call__(self, environ, start_response):
        def custom_start_response(status, headers, exc_info=None):
            headers.append(('Result', 'OK'))
            return start_response(status, headers, exc_info)
        return self.app(environ, custom_start_response)


class User(types.Type):
    name = validators.String()


def get_endpoint():
    return None


routes = [
    Route(url='/get-endpoint/', method='GET', handler=get_endpoint),
]
app = App(routes=routes)


def test_wsgi_middleware():
    wrapped_app = WSGIMiddleware(app)
    test_client = TestClient(wrapped_app)

    response = test_client.get('/get-endpoint')
    assert response.status_code == 200
    assert response.headers['Result'] == 'OK'
