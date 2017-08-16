from apistar import Route, TestClient, typesystem
from apistar.frameworks.wsgi import WSGIApp as App


class MinMaxNumber(typesystem.Number):
    minimum = -3.0
    maximum = 3.0
    exclusive_minimum = True
    exclusive_maximum = True


class MultipleNumber(typesystem.Number):
    multiple_of = 0.1


def get_min_max(value: MinMaxNumber):
    return {'value': value}


def get_multiple(value: MultipleNumber):
    return {'value': value}


app = App(routes=[
    Route('/min_max/', 'GET', get_min_max),
    Route('/multiple/', 'GET', get_multiple),
])


client = TestClient(app)


def test_invalid_numberr():
    response = client.get('/min_max/?value=a')
    assert response.status_code == 400
    assert response.json() == {'value': 'Must be a valid number.'}


def test_finite_numberr():
    response = client.get('/min_max/?value=inf')
    assert response.status_code == 400
    assert response.json() == {'value': 'Must be a finite number.'}


def test_valid_min_max():
    response = client.get('/min_max/?value=2.9')
    assert response.status_code == 200
    assert response.json() == {'value': 2.9}

    response = client.get('/min_max/?value=-2.9')
    assert response.status_code == 200
    assert response.json() == {'value': -2.9}


def test_invalid_min_max():
    response = client.get('/min_max/?value=3')
    assert response.status_code == 400
    assert response.json() == {'value': 'Must be less than 3.0.'}

    response = client.get('/min_max/?value=-3')
    assert response.status_code == 400
    assert response.json() == {'value': 'Must be greater than -3.0.'}


def test_valid_multiple():
    response = client.get('/multiple/?value=1.2')
    assert response.status_code == 200
    assert response.json() == {'value': 1.2}


def test_invalid_multiple():
    response = client.get('/multiple/?value=1.23')
    assert response.status_code == 400
    assert response.json() == {'value': 'Must be a multiple of 0.1.'}
