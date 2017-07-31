import pytest

from apistar import App, Route, TestClient, exceptions, typesystem


class UntypedList(typesystem.Array):
    pass


class TypedList(typesystem.Array):
    items = typesystem.Integer


def basic_untyped_list(things: UntypedList):
    return things


def basic_typed_list(things: TypedList):
    return things


routes = [
    Route('/basic_typed_list/', 'POST', basic_typed_list),
    Route('/basic_untyped_list/', 'POST', basic_untyped_list),
]

app = App(routes=routes)
client = TestClient(app)


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
    NewTypedList = typesystem.Array(items=typesystem.Number)
    assert NewTypedList([1.1, 2.2, 3.3]) == [1.1, 2.2, 3.3]
    with pytest.raises(exceptions.SchemaError) as exc:
        NewTypedList([1, 2, 'c'])
    assert 'Must be a valid number.' in str(exc.value)


def test_array_specific_single_item():
    SpecificTypeList = typesystem.Array(items=typesystem.Number)

    assert SpecificTypeList([1, 2, 3, 4.5]) == [1, 2, 3, 4.5]
    assert SpecificTypeList([]) == []

    with pytest.raises(exceptions.SchemaError) as exc:
        SpecificTypeList([1, 'two', 3])
    assert 'Must be a valid number.' in str(exc.value)


def test_array_specific_items_no_additional():
    SpecificTypedList = typesystem.Array(items=[
        typesystem.Number,
        typesystem.String,
        typesystem.Boolean
    ], additional_items=False)

    assert SpecificTypedList([23, 'twenty-three', True]) == \
        [23, 'twenty-three', True]

    with pytest.raises(exceptions.SchemaError) as exc:
        SpecificTypedList([23, 'twenty-three'])
    assert str(exc.value) == 'Not enough items.'

    with pytest.raises(exceptions.SchemaError) as exc:
        SpecificTypedList([23, 'twenty-three', True, False])
    assert str(exc.value) == 'Too many items.'

    with pytest.raises(exceptions.SchemaError) as exc:
        SpecificTypedList(['.', 'twenty-three', True])
    assert 'Must be a valid number.' in str(exc.value)


def test_array_specific_items_with_additional():
    SpecificTypedList = typesystem.Array(items=[
        typesystem.Number,
        typesystem.String,
        typesystem.Boolean
    ], additional_items=True)

    assert SpecificTypedList([23, 'twenty-three', True]) == \
        [23, 'twenty-three', True]

    with pytest.raises(exceptions.SchemaError) as exc:
        SpecificTypedList([23, 'twenty-three'])
    assert str(exc.value) == 'Not enough items.'

    assert SpecificTypedList([23, 'twenty-three', True, False]) == \
        [23, 'twenty-three', True, False]


def test_array_min_items():
    MinimumItemList = typesystem.Array(min_items=2)

    assert MinimumItemList([1, 2]) == [1, 2]
    assert MinimumItemList([1, 2] * 10) == [1, 2] * 10

    with pytest.raises(exceptions.SchemaError) as exc:
        MinimumItemList([])
    assert str(exc.value) == 'Not enough items.'

    with pytest.raises(exceptions.SchemaError) as exc:
        MinimumItemList([1])
    assert str(exc.value) == 'Not enough items.'


def test_array_max_items():
    MaximumItemList = typesystem.Array(max_items=3)

    assert MaximumItemList([1, 2]) == [1, 2]
    assert MaximumItemList([]) == []

    with pytest.raises(exceptions.SchemaError) as exc:
        MaximumItemList([1, 2, 3, 4, 5])
    assert str(exc.value) == 'Too many items.'

    with pytest.raises(exceptions.SchemaError) as exc:
        MaximumItemList([1] * 50)
    assert str(exc.value) == 'Too many items.'


def test_array_unique_items():
    UniqueItemList = typesystem.Array(unique_items=True)

    assert UniqueItemList([1, 2, 3, 4, 5]) == [1, 2, 3, 4, 5]
    assert UniqueItemList([]) == []

    with pytest.raises(exceptions.SchemaError) as exc:
        UniqueItemList([1, 2, 3, 4, 1])
    assert 'This item is not unique.' in str(exc.value)
