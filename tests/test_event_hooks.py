from apistar import App, Route, exceptions, http, test


class CustomResponseHeader():
    def on_response(self, response: http.Response):
        response.headers['Custom'] = 'Ran on_response'
        return response

    def on_error(self, response: http.Response):
        response.headers['Custom'] = 'Ran on_error'
        return response


def hello_world():
    return {'hello': 'world'}


def error():
    raise exceptions.BadRequest()


routes = [
    Route('/hello', method='GET', handler=hello_world),
    Route('/error', method='GET', handler=error),
]

event_hooks = [CustomResponseHeader()]

app = App(routes=routes, event_hooks=event_hooks)

client = test.TestClient(app)


def test_on_response():
    response = client.get('/hello')
    assert response.status_code == 200
    assert response.headers['Custom'] == 'Ran on_response'


def test_on_error():
    response = client.get('/error')
    assert response.status_code == 400
    assert response.headers['Custom'] == 'Ran on_error'
