import typing

from apistar import Route, test, types, validators
from apistar.server.app import App


def str_path_param(param: str):
    return {'param': param}


def int_path_param(param: int):
    return {'param': param}


def str_query_param(param: str):
    return {'param': param}


def int_query_param(param: int):
    return {'param': param}


def bool_query_param(param: bool):
    return {'param': param}


def str_query_param_with_default(param: str=''):
    return {'param': param}


def int_query_param_with_default(param: int=None):
    return {'param': param}


def bool_query_param_with_default(param: bool=False):
    return {'param': param}


def str_list_query_param(param: typing.List[str]):
    return {'param': param}


def str_list_query_param_with_default(param: typing.List[str]=[]):
    return {'param': param}


def int_list_query_param(param: typing.List[int]):
    return {'param': param}


def int_list_query_param_with_default(param: typing.List[int]=[]):
    return {'param': param}


def bool_list_query_param(param: typing.List[bool]):
    return {'param': param}


def bool_list_query_param_with_default(param: typing.List[bool]=[]):
    return {'param': param}


def float_list_query_param(param: typing.List[float]):
    return {'param': param}


def float_list_query_param_with_default(param: typing.List[float]=[]):
    return {'param': param}


class User(types.Type):
    name = validators.String(max_length=10)
    age = validators.Integer(minimum=0, allow_null=True, default=None)


def type_body_param(user: User):
    return {"user": user}


routes = [
    # Path parameters
    Route(url='/str_path_param/{param}/', method='GET', handler=str_path_param),
    Route(url='/int_path_param/{param}/', method='GET', handler=int_path_param),

    # Query parameters
    Route(url='/str_query_param/', method='GET', handler=str_query_param),
    Route(url='/int_query_param/', method='GET', handler=int_query_param),
    Route(url='/bool_query_param/', method='GET', handler=bool_query_param),
    Route(url='/str_query_param_with_default/', method='GET', handler=str_query_param_with_default),
    Route(url='/int_query_param_with_default/', method='GET', handler=int_query_param_with_default),
    Route(url='/bool_query_param_with_default/', method='GET', handler=bool_query_param_with_default),

    # Query parameters with List[]
    Route(url='/str_list_query_param/', method='GET', handler=str_list_query_param),
    Route(url='/str_list_query_param_with_default/', method='GET', handler=str_list_query_param_with_default),
    Route(url='/int_list_query_param/', method='GET', handler=int_list_query_param),
    Route(url='/int_list_query_param_with_default/', method='GET', handler=int_list_query_param_with_default),
    Route(url='/bool_list_query_param/', method='GET', handler=bool_list_query_param),
    Route(url='/bool_list_query_param_with_default/', method='GET', handler=bool_list_query_param_with_default),
    Route(url='/float_list_query_param/', method='GET', handler=float_list_query_param),
    Route(url='/float_list_query_param_with_default/', method='GET', handler=float_list_query_param_with_default),

    # Body parameters
    Route(url='/type_body_param/', method='POST', handler=type_body_param),
]

app = App(routes=routes)
client = test.TestClient(app)


def test_str_path_param():
    response = client.get('/str_path_param/123/')
    assert response.json() == {'param': '123'}


def test_int_path_param():
    response = client.get('/int_path_param/123/')
    assert response.json() == {'param': 123}


def test_str_query_param():
    response = client.get('/str_query_param/?param=123')
    assert response.json() == {'param': '123'}

    response = client.get('/str_query_param/')
    assert response.json() == {'param': 'This field is required.'}


def test_str_query_param_with_default():
    response = client.get('/str_query_param_with_default/?param=123')
    assert response.json() == {'param': '123'}

    response = client.get('/str_query_param_with_default/')
    assert response.json() == {'param': ''}


def test_int_query_param():
    response = client.get('/int_query_param/?param=123')
    assert response.json() == {'param': 123}

    response = client.get('/int_query_param/')
    assert response.json() == {'param': 'This field is required.'}


def test_int_query_param_with_default():
    response = client.get('/int_query_param_with_default/?param=123')
    assert response.json() == {'param': 123}

    response = client.get('/int_query_param_with_default/')
    assert response.json() == {'param': None}


def test_bool_query_param():
    response = client.get('/bool_query_param/?param=true')
    assert response.json() == {'param': True}

    response = client.get('/bool_query_param/?param=false')
    assert response.json() == {'param': False}

    response = client.get('/bool_query_param/')
    assert response.json() == {'param': 'This field is required.'}


def test_bool_query_param_with_default():
    response = client.get('/bool_query_param_with_default/?param=true')
    assert response.json() == {'param': True}

    response = client.get('/bool_query_param_with_default/?param=false')
    assert response.json() == {'param': False}

    response = client.get('/bool_query_param_with_default/')
    assert response.json() == {'param': False}


def test_str_list_query_param():
    response = client.get('/str_list_query_param/?param=a&param=b')
    assert response.json() == {'param': ['a', 'b']}

    response = client.get('/str_list_query_param/?param=a')
    assert response.json() == {'param': ['a']}

    response = client.get('/str_query_param/')
    assert response.json() == {'param': 'This field is required.'}


def test_str_list_query_param_with_default():
    response = client.get('/str_list_query_param_with_default/?param=a&param=b')
    assert response.json() == {'param': ['a', 'b']}

    response = client.get('/str_list_query_param/?param=a')
    assert response.json() == {'param': ['a']}

    response = client.get('/str_list_query_param_with_default/')
    assert response.json() == {'param': []}


def test_int_list_query_param():
    response = client.get('/int_list_query_param/?param=4&param=2')
    assert response.json() == {'param': [4, 2]}

    response = client.get('/int_list_query_param/?param=4')
    assert response.json() == {'param': [4]}

    response = client.get('/int_query_param/')
    assert response.json() == {'param': 'This field is required.'}


def test_int_list_query_param_with_default():
    response = client.get('/int_list_query_param_with_default/?param=4&param=2')
    assert response.json() == {'param': [4, 2]}

    response = client.get('/int_list_query_param/?param=4')
    assert response.json() == {'param': [4]}

    response = client.get('/int_list_query_param_with_default/')
    assert response.json() == {'param': []}


def test_bool_list_query_param():
    response = client.get('/bool_list_query_param/?param=True&param=False')
    assert response.json() == {'param': [True, False]}

    response = client.get('/bool_list_query_param/?param=True')
    assert response.json() == {'param': [True]}

    response = client.get('/bool_list_query_param/?param=False')
    assert response.json() == {'param': [False]}

    response = client.get('/bool_query_param/')
    assert response.json() == {'param': 'This field is required.'}


def test_bool_list_query_param_with_default():
    response = client.get('/bool_list_query_param_with_default/?param=True&param=False')
    assert response.json() == {'param': [True, False]}

    response = client.get('/bool_list_query_param/?param=True')
    assert response.json() == {'param': [True]}

    response = client.get('/bool_list_query_param/?param=False')
    assert response.json() == {'param': [False]}

    response = client.get('/bool_list_query_param_with_default/')
    assert response.json() == {'param': []}


def test_float_list_query_param():
    response = client.get('/float_list_query_param/?param=3.14&param=3.15')
    assert response.json() == {'param': [3.14, 3.15]}

    response = client.get('/float_list_query_param/?param=3.14')
    assert response.json() == {'param': [3.14]}

    response = client.get('/float_list_query_param/')
    assert response.json() == {'param': 'This field is required.'}


def test_float_list_query_param_with_default():
    response = client.get('/float_list_query_param_with_default/?param=3.14&param=3.15')
    assert response.json() == {'param': [3.14, 3.15]}

    response = client.get('/float_list_query_param/?param=3.14')
    assert response.json() == {'param': [3.14]}

    response = client.get('/float_list_query_param_with_default/')
    assert response.json() == {'param': []}


def test_type_body_param():
    response = client.post('/type_body_param/', json={'name': 'tom'})
    assert response.json() == {'user': {'name': 'tom', 'age': None}}

    response = client.post('/type_body_param/', json={'name': 'x' * 100})
    assert response.status_code == 400
    assert response.json() == {'name': 'Must have no more than 10 characters.'}

    response = client.post('/type_body_param/', json={})
    assert response.status_code == 400
    assert response.json() == {'name': 'This field is required.'}
