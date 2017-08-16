from apistar import Route, TestClient, typesystem
from apistar.frameworks.wsgi import WSGIApp as App


class MinMaxInteger(typesystem.Integer):
    minimum = -3
    maximum = 3


class MultipleInteger(typesystem.Integer):
    multiple_of = 10


def get_min_max(value: MinMaxInteger):
    return {'value': value}


def get_multiple(value: MultipleInteger):
    return {'value': value}


app = App(routes=[
    Route('/min_max/', 'GET', get_min_max),
    Route('/multiple/', 'GET', get_multiple),
])


client = TestClient(app)


def test_invalid_integer():
    response = client.get('/min_max/?value=a')
    assert response.status_code == 400
    assert response.json() == {'value': 'Must be a valid number.'}


def test_valid_min_max():
    response = client.get('/min_max/?value=3')
    assert response.status_code == 200
    assert response.json() == {'value': 3}

    response = client.get('/min_max/?value=-3')
    assert response.status_code == 200
    assert response.json() == {'value': -3}


def test_invalid_min_max():
    response = client.get('/min_max/?value=4')
    assert response.status_code == 400
    assert response.json() == {'value': 'Must be less than or equal to 3.'}

    response = client.get('/min_max/?value=-4')
    assert response.status_code == 400
    assert response.json() == {'value': 'Must be greater than or equal to -3.'}


def test_valid_multiple():
    response = client.get('/multiple/?value=50')
    assert response.status_code == 200
    assert response.json() == {'value': 50}


def test_invalid_multiple():
    response = client.get('/multiple/?value=55')
    assert response.status_code == 400
    assert response.json() == {'value': 'Must be a multiple of 10.'}
