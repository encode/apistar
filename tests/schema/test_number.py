from apistar import app, routing, schema, test


class MinMaxNumber(schema.Number):
    minimum = -3.0
    maximum = 3.0
    exclusive_minimum = True
    exclusive_maximum = True


class MultipleNumber(schema.Number):
    multiple_of = 0.1


def get_min_max(value: MinMaxNumber):
    return {'value': value}


def get_multiple(value: MultipleNumber):
    return {'value': value}


app = app.App(routes=[
    routing.Route('/min_max/', 'GET', get_min_max),
    routing.Route('/multiple/', 'GET', get_multiple),
])


client = test.TestClient(app)


def test_invalid_numberr():
    response = client.get('/min_max/?value=a')
    assert response.status_code == 400
    assert response.json() == {'message': 'Must be a valid number.'}


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
    assert response.json() == {'message': 'Must be less than 3.0.'}

    response = client.get('/min_max/?value=-3')
    assert response.status_code == 400
    assert response.json() == {'message': 'Must be greater than -3.0.'}


def test_valid_multiple():
    response = client.get('/multiple/?value=1.2')
    assert response.status_code == 200
    assert response.json() == {'value': 1.2}


def test_invalid_multiple():
    response = client.get('/multiple/?value=1.23')
    assert response.status_code == 400
    assert response.json() == {'message': 'Must be a multiple of 0.1.'}
