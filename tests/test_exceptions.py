from apistar import App, Route
from apistar.exceptions import APIException
from apistar.test import TestClient


def exc():
    raise APIException(message='error', status_code=400)


app = App(routes=[
    Route('/exc/', 'GET', exc),
])


client = TestClient(app)


def test_exc():
    response = client.get('/exc/')
    assert response.status_code == 400
    assert response.json() == {
        'message': 'error'
    }
