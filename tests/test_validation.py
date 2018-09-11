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


class User(types.Type):
    name = validators.String(max_length=10)
    age = validators.Integer(minimum=0, allow_null=True, default=None)


def type_body_param(user: User):
    return {"user": user}


class ApiKey(types.Type):
    api_key = validators.String(length=32)
    api_secret = validators.String(min_length=16, max_length=16)


def type_body_param2(api_key: ApiKey):
    return {"api_key": api_key}


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

    # Body parameters
    Route(url='/type_body_param/', method='POST', handler=type_body_param),
    Route(url='/type_body_param2/', method='POST', handler=type_body_param2),
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
    assert response.json() == {'param': 'The "param" field is required.'}


def test_str_query_param_with_default():
    response = client.get('/str_query_param_with_default/?param=123')
    assert response.json() == {'param': '123'}

    response = client.get('/str_query_param_with_default/')
    assert response.json() == {'param': ''}


def test_int_query_param():
    response = client.get('/int_query_param/?param=123')
    assert response.json() == {'param': 123}

    response = client.get('/int_query_param/')
    assert response.json() == {'param': 'The "param" field is required.'}


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
    assert response.json() == {'param': 'The "param" field is required.'}


def test_bool_query_param_with_default():
    response = client.get('/bool_query_param_with_default/?param=true')
    assert response.json() == {'param': True}

    response = client.get('/bool_query_param_with_default/?param=false')
    assert response.json() == {'param': False}

    response = client.get('/bool_query_param_with_default/')
    assert response.json() == {'param': False}


def test_type_body_param():
    response = client.post('/type_body_param/', json={'name': 'tom'})
    assert response.json() == {'user': {'name': 'tom', 'age': None}}

    response = client.post('/type_body_param/', json={'name': 'x' * 100})
    assert response.status_code == 400
    assert response.json() == {'name': 'Must have no more than 10 characters.'}

    response = client.post('/type_body_param/', json={})
    assert response.status_code == 400
    assert response.json() == {'name': 'The "name" field is required.'}


def test_type_body_param2():
    response = client.post('/type_body_param2/', json={'api_key': 'x' * 32, 'api_secret': 'y' * 16})
    assert response.json() == {'api_key': {'api_key': 'x' * 32, 'api_secret': 'y' * 16}}

    response = client.post('/type_body_param2/', json={'api_key': 'x', 'api_secret': 'y' * 16})
    assert response.status_code == 400
    assert response.json() == {'api_key': 'Must have exactly 32 characters.'}

    response = client.post('/type_body_param2/', json={'api_key': 'x' * 32, 'api_secret': 'y'})
    assert response.status_code == 400
    assert response.json() == {'api_secret': 'Must have exactly 16 characters.'}

    response = client.post('/type_body_param2/', json={'api_key': 'x' * 100, 'api_secret': 'y' * 16})
    assert response.status_code == 400
    assert response.json() == {'api_key': 'Must have exactly 32 characters.'}

    response = client.post('/type_body_param2/', json={'api_key': 'x' * 32, 'api_secret': 'y' * 100})
    assert response.status_code == 400
    assert response.json() == {'api_secret': 'Must have exactly 16 characters.'}
