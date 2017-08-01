import pytest

from apistar import App, Route, TestClient, exceptions, typesystem


def get_boolean(value: typesystem.Boolean):
    return {'value': value}


app = App(routes=[
    Route('/boolean/', 'GET', get_boolean),
])


client = TestClient(app)


def test_boolean():
    assert typesystem.Boolean(1) is True
    assert typesystem.Boolean(0) is False
    assert typesystem.Boolean('1') is True
    assert typesystem.Boolean('0') is False
    assert typesystem.Boolean(True) is True
    assert typesystem.Boolean(False) is False
    assert typesystem.Boolean('TRUE') is True
    assert typesystem.Boolean('FALSE') is False


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
    CustomBool = typesystem.newtype('Boolean', errors={'type': 'Must be true or false.'})
    with pytest.raises(exceptions.TypeSystemError) as exc:
        CustomBool('invalid')
    assert str(exc.value) == 'Must be true or false.'
