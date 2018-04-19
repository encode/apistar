import pytest

from apistar import App, Route, http, test

ON_ERROR = None


class CustomResponseHeader():
    def on_request(self):
        self.message = 'Ran hooks'

    def on_response(self, response: http.Response):
        response.headers['Custom'] = self.message

    def on_error(self):
        global ON_ERROR
        ON_ERROR = 'Ran on_error'


def hello_world():
    return {'hello': 'world'}


def error():
    assert 1 == 2


routes = [
    Route('/hello', method='GET', handler=hello_world),
    Route('/error', method='GET', handler=error),
]

event_hooks = [CustomResponseHeader]

app = App(routes=routes, event_hooks=event_hooks)

client = test.TestClient(app)


def test_on_response():
    response = client.get('/hello')
    assert response.status_code == 200
    assert response.headers['Custom'] == 'Ran hooks'


def test_on_error():
    global ON_ERROR

    ON_ERROR = None
    with pytest.raises(AssertionError):
        client.get('/error')
    assert ON_ERROR == 'Ran on_error'
