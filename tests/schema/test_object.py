import pytest

from apistar import app, exceptions, routing, schema, test


class Location(schema.Object):
    properties = {
        'latitude': schema.Number(minimum=-90.0, maximum=90.0),
        'longitude': schema.Number(minimum=-180.0, maximum=180.0)
    }


class HighScore(schema.Object):
    properties = {
        'name': schema.String(max_length=100),
        'score': schema.Integer(minimum=0, maximum=100),
        'completed': schema.Boolean(default=False),
        'difficulty': schema.Enum(enum=['easy', 'medium', 'hard']),
        'location': Location(default={'latitude': 0.0, 'longitude': 0.0})
    }


def basic_object(score: HighScore):
    return score


routes = [
    routing.Route('/basic_object/', 'POST', basic_object),
]

app = app.App(routes=routes)
client = test.TestClient(app)


def test_valid_object():
    response = client.post('/basic_object/', json={
        'name': 'tom',
        'score': 87,
        'difficulty': 'easy',
        'completed': True,
        'location': {
            'latitude': 51.477,
            'longitude': 0.0
        }
    })
    assert response.status_code == 200
    assert response.json() == {
        'name': 'tom',
        'score': 87,
        'difficulty': 'easy',
        'completed': True,
        'location': {
            'latitude': 51.477,
            'longitude': 0.0
        }
    }


def test_invalid_object():
    response = client.post('/basic_object/', json={
        'score': 105,
        'difficulty': 'foo'
    })
    assert response.status_code == 400
    assert response.json() == {
        'name': 'This field is required.',
        'difficulty': 'Must be a valid choice.',
        'score': 'Must be less than or equal to 100.'
    }


class test_object_instantiation():
    location = Location({'latitude': 51.477, 'longitude': 0.0})
    value = HighScore({
        'name': 'tom',
        'score': 99.0,
        'difficulty': 'easy',
        'completed': 'True',
        'location': location
    })
    assert value['name'] == 'tom'
    assert value['score'] == 99
    assert value['completed'] is True
    assert value['location'] == location


class test_object_default():
    value = HighScore({
        'name': 'tom',
        'score': 99,
        'difficulty': 'easy',
        'completed': True
    })
    assert value['location'] == {'latitude': 0.0, 'longitude': 0.0}


class test_object_invalid_key():
    with pytest.raises(exceptions.SchemaError) as exc:
        HighScore({1: 'invalid'})
    assert str(exc.value) == 'Object keys must be strings.'


class test_object_invalid_type():
    with pytest.raises(exceptions.SchemaError) as exc:
        HighScore(1)
    assert str(exc.value) == 'Must be an object.'
