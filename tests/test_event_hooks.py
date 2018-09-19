import pytest

from apistar import App, Component, Route, http, test

ON_ERROR = None


class CustomResponseHeader():
    def on_request(self):
        self.message = 'Ran hooks'

    def on_response(self, response: http.Response):
        response.headers['Custom'] = self.message

    def on_error(self):
        global ON_ERROR
        ON_ERROR = 'Ran on_error'


A_INSTANCES = []


class A:
    pass


class AComponent(Component):
    def resolve(self) -> A:
        return A()


class AEventHooks:
    def on_request(self, a: A):
        global A_INSTANCES
        A_INSTANCES = [a]

    def on_response(self, a: A):
        A_INSTANCES.append(a)

    def on_error(self, a: A):
        A_INSTANCES.append(a)


def hello_world():
    return {'hello': 'world'}


def uses_a(a: A):
    A_INSTANCES.append(a)
    raise RuntimeError('something bad happened')


def error():
    assert 1 == 2


routes = [
    Route('/hello', method='GET', handler=hello_world),
    Route('/error', method='GET', handler=error),
    Route('/uses-a', method='GET', handler=uses_a),
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


def test_on_error_loads_the_same_component_instances():
    # Given that I have an app that uses an AComponent and the AEventHooks
    app = App(
        components=[AComponent()],
        event_hooks=[AEventHooks],
        routes=[Route('/uses-a', method='GET', handler=uses_a)],
    )

    # When I call an endpoint that raises an error
    with pytest.raises(RuntimeError):
        test.TestClient(app).get('/uses-a')

    # Then all the instances of A are the same
    assert len(A_INSTANCES) >= 2
    for i in range(1, len(A_INSTANCES)):
        assert A_INSTANCES[i] is A_INSTANCES[i - 1]
