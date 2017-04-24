from apistar import app, routing, schema, test


class Color(schema.Enum):
    errors = {'enum': 'Must be a valid color.'}
    enum = ['red', 'green', 'blue']


class TermsAndConditions(schema.Enum):
    errors = {'exact': 'You must agree to the terms and conditions to proceed.'}
    enum = ['yes']


def validate_color(value: Color):
    return {'value': value}


def validate_terms(value: TermsAndConditions):
    return {'value': value}


app = app.App(routes=[
    routing.Route('/color/', 'GET', validate_color),
    routing.Route('/terms/', 'GET', validate_terms),
])


client = test.TestClient(app)


def test_valid_enum():
    response = client.get('/color/?value=red')
    assert response.status_code == 200
    assert response.json() == {'value': 'red'}


def test_valid_literal():
    response = client.get('/terms/?value=yes')
    assert response.status_code == 200
    assert response.json() == {'value': 'yes'}


def test_invalid_enum():
    response = client.get('/color/?value=foo')
    assert response.status_code == 400
    assert response.json() == {'message': 'Must be a valid color.'}


def test_invalid_literal():
    response = client.get('/terms/?value=foo')
    assert response.status_code == 400
    assert response.json() == {'message': 'You must agree to the terms and conditions to proceed.'}
