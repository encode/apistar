from apistar import app, routing, schema, test


def get_boolean(value: schema.Boolean):
    return {'value': value}


app = app.App(routes=[
    routing.Route('/boolean/', 'GET', get_boolean),
])


client = test.TestClient(app)


def test_valid_boolean():
    response = client.get('/boolean/?value=true')
    assert response.status_code == 200
    assert response.json() == {'value': True}

    response = client.get('/boolean/?value=false')
    assert response.status_code == 200
    assert response.json() == {'value': False}


def test_invalid_boolean():
    response = client.get('/boolean/?value=a')
    assert response.status_code == 400
    assert response.json() == {'message': 'Must be a valid boolean.'}
