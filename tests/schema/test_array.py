import pytest

from apistar import app, exceptions, routing, schema, test


class UntypedList(schema.Array):
    item_type = None


class TypedList(schema.Array):
    item_type = schema.Integer


def basic_untyped_list(things: UntypedList):
    return things


def basic_typed_list(things: TypedList):
    return things


routes = [
    routing.Route('/basic_typed_list/', 'POST', basic_typed_list),
    routing.Route('/basic_untyped_list/', 'POST', basic_untyped_list),
]

app = app.App(routes=routes)
client = test.TestClient(app)


def test_valid_untyped_list():
    payload = [
        'foo',
        'bar',
        1,
        3.1415927,
        'baz',
        True,
        None,
        'qux',
        ['tribbles'] * 23,
        {'foo': 'bar', 'baz': 'qux'},
    ]

    response = client.post('/basic_untyped_list/', json=payload)
    assert response.status_code == 200
    assert response.json() == payload


def test_valid_typed_list():
    payload = list(range(0, 10))

    response = client.post('/basic_typed_list/', json=payload)
    assert response.status_code == 200
    assert response.json() == payload


def test_invalid_typed_list():
    payload = [1, 2, 'three', 4, '5ive']

    response = client.post('/basic_typed_list/', json=payload)
    assert response.status_code == 400
    assert response.json() == {
        '2': 'Must be a valid number.',
        '4': 'Must be a valid number.',
    }


def test_array_instantiation():
    typed = TypedList([0, 1, 2])
    untyped = UntypedList([1, 'two', 3.3333, True, None])

    for x in range(0, 3):
        assert typed[x] == x

    assert untyped[0] == 1
    assert untyped[1] == 'two'
    assert untyped[2] == 3.3333
    assert untyped[3] is True
    assert untyped[4] is None


def test_array_invalid_type():
    with pytest.raises(exceptions.SchemaError) as exc:
        UntypedList(1)
    assert str(exc.value) == 'Must be a list.'


def test_array_kwargs():
    NewTypedList = schema.Array(item_type=float)
    assert NewTypedList([1.1, 2.2, 3.3]) == [1.1, 2.2, 3.3]
