from apistar import Route, TestClient, typesystem
from apistar.frameworks.wsgi import WSGIApp as App


class MinMaxLength(typesystem.String):
    min_length = 5
    max_length = 10


class NotBlank(typesystem.String):
    min_length = 1


class ValidPattern(typesystem.String):
    pattern = '^[A-Za-z0-9_]+$'


def validate_length(value: MinMaxLength):
    return {'value': value}


def validate_not_blank(value: NotBlank):
    return {'value': value}


def validate_pattern(value: ValidPattern):
    return {'value': value}


app = App(routes=[
    Route('/length/', 'GET', validate_length),
    Route('/not_blank/', 'GET', validate_not_blank),
    Route('/pattern/', 'GET', validate_pattern),
])


client = TestClient(app)


def test_valid_length():
    response = client.get('/length/?value=abcde')
    assert response.status_code == 200
    assert response.json() == {'value': 'abcde'}

    response = client.get('/length/?value=abcdefghij')
    assert response.status_code == 200
    assert response.json() == {'value': 'abcdefghij'}


def test_invalid_length():
    response = client.get('/length/?value=abcd')
    assert response.status_code == 400
    assert response.json() == {'value': 'Must have at least 5 characters.'}

    response = client.get('/length/?value=abcdefghijk')
    assert response.status_code == 400
    assert response.json() == {'value': 'Must have no more than 10 characters.'}


def test_valid_not_blank():
    response = client.get('/not_blank/?value=a')
    assert response.status_code == 200
    assert response.json() == {'value': 'a'}


def test_invalid_not_blank():
    response = client.get('/not_blank/?value=')
    assert response.status_code == 400
    assert response.json() == {'value': 'Must not be blank.'}


def test_valid_pattern():
    response = client.get('/pattern/?value=aA0')
    assert response.status_code == 200
    assert response.json() == {'value': 'aA0'}


def test_invalid_pattern():
    response = client.get('/pattern/?value=aA@0')
    assert response.status_code == 400
    assert response.json() == {'value': 'Must match the pattern /^[A-Za-z0-9_]+$/.'}

    response = client.get('/pattern/?value=')
    assert response.status_code == 400
    assert response.json() == {'value': 'Must match the pattern /^[A-Za-z0-9_]+$/.'}
