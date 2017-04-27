import pytest

from apistar import app, exceptions, routing, schema, test


def get_boolean(value: schema.Boolean):
    return {'value': value}


app = app.App(routes=[
    routing.Route('/boolean/', 'GET', get_boolean),
])


client = test.TestClient(app)


def test_boolean():
    assert schema.Boolean(1) is True
    assert schema.Boolean(0) is False
    assert schema.Boolean('1') is True
    assert schema.Boolean('0') is False
    assert schema.Boolean(True) is True
    assert schema.Boolean(False) is False
    assert schema.Boolean('TRUE') is True
    assert schema.Boolean('FALSE') is False


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
    assert response.json() == {'value': 'Must be a valid boolean.'}


def test_boolean_kwargs():
    CustomBool = schema.Boolean(errors={'type': 'Must be true or false.'})
    with pytest.raises(exceptions.SchemaError) as exc:
        CustomBool('invalid')
    assert str(exc.value) == 'Must be true or false.'
