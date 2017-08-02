from typing import List

from apistar import App, Route, TestClient, typesystem


class KittenName(typesystem.String):
    max_length = 100


class KittenColor(typesystem.Enum):
    enum = [
        'black',
        'brown',
        'white',
        'grey',
        'tabby'
    ]


class Kitten(typesystem.Object):
    properties = {
        'name': KittenName,
        'color': KittenColor,
        'cuteness': typesystem.newtype(
            'Number',
            minimum=0.0,
            maximum=10.0,
            multiple_of=0.1
        )
    }


def list_favorite_kittens(color: KittenColor) -> List[Kitten]:
    """
    List your favorite kittens, optionally filtered by color.
    """
    kittens = [
        Kitten({'name': 'fluffums', 'color': 'white', 'cuteness': 9.8}),
        Kitten({'name': 'tabitha', 'color': 'tabby', 'cuteness': 8.7}),
        Kitten({'name': 'meowster', 'color': 'white', 'cuteness': 7.8}),
        Kitten({'name': 'fuzzball', 'color': 'brown', 'cuteness': 8.0}),
    ]
    return [
        kitten for kitten in kittens
        if kitten['color'] == color
    ]


def add_favorite_kitten(name: KittenName) -> Kitten:
    """
    Add a kitten to your favorites list.
    """
    return Kitten({'name': name, 'color': 'black', 'cuteness': 0.0})


app = App(routes=[
    Route('/list_favorite_kittens/', 'GET', list_favorite_kittens),
    Route('/add_favorite_kitten/', 'POST', add_favorite_kitten),
])


client = TestClient(app)


def test_list_kittens():
    response = client.get('/list_favorite_kittens/?color=white')
    assert response.status_code == 200
    assert response.json() == [
        {'name': 'fluffums', 'color': 'white', 'cuteness': 9.8},
        {'name': 'meowster', 'color': 'white', 'cuteness': 7.8}
    ]


def test_add_kitten():
    response = client.post('/add_favorite_kitten/?name=charlie')
    assert response.status_code == 200
    assert response.json() == {
        'name': 'charlie', 'color': 'black', 'cuteness': 0.0
    }


def test_invalid_list_kittens():
    response = client.get('/list_favorite_kittens/?color=invalid')
    assert response.status_code == 400
    assert response.json() == {
        'color': 'Must be a valid choice.'
    }


def test_empty_arg_as_query_param():
    def view(arg):
        return {'arg': arg}

    routes = [
        Route('/', 'GET', view)
    ]
    app = App(routes=routes)
    client = TestClient(app)
    response = client.get('/?arg=123')
    assert response.json() == {
        'arg': '123'
    }


def test_cannot_coerce_query_param():
    def view(arg: int):
        return {'arg': arg}

    routes = [
        Route('/', 'GET', view)
    ]
    app = App(routes=routes)
    client = TestClient(app)
    response = client.get('/?arg=abc')
    assert response.json() == {
        'arg': None
    }


def test_arg_as_composite_param():
    def view(arg: dict):
        return {'arg': arg}

    routes = [
        Route('/', 'POST', view)
    ]
    app = App(routes=routes)
    client = TestClient(app)
    response = client.post('/', json={'a': 123})
    assert response.json() == {
        'arg': {'a': 123}
    }
