from apistar import app, routing, schema, test


class MinMaxInteger(schema.Integer):
    minimum = -3
    maximum = 3


class MultipleInteger(schema.Integer):
    multiple_of = 10


def get_min_max(value: MinMaxInteger):
    return {'value': value}


def get_multiple(value: MultipleInteger):
    return {'value': value}


app = app.App(routes=[
    routing.Route('/min_max/', 'GET', get_min_max),
    routing.Route('/multiple/', 'GET', get_multiple),
])


client = test.TestClient(app)


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
