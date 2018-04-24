import pytest
from pytest import param

from apistar import Route, http, test
from apistar.server.app import App, ASyncApp

# HTTP Components as parameters


def get_request(request: http.Request):
    return {
        'method': request.method,
        'url': request.url,
        'headers': dict(request.headers),
        'body': request.body.decode('utf-8')
    }


def get_method(method: http.Method):
    return {'method': method}


def get_scheme(scheme: http.Scheme):
    return {'scheme': scheme}


def get_host(host: http.Host):
    return {'host': host}


def get_port(port: http.Port):
    return {'port': port}


def get_path(path: http.Path):
    return {'path': path}


def get_query_string(query_string: http.QueryString):
    return {'query_string': query_string}


def get_query_params(query_string: http.QueryString, query_params: http.QueryParams):
    return {'query_params': dict(query_params)}


def get_page_query_param(page: http.QueryParam):
    return {'page': page}


def get_url(url: http.URL):
    return {'url': url, 'url.components': url.components}


def get_body(body: http.Body):
    return {'body': body.decode('utf-8')}


def get_headers(headers: http.Headers):
    return {'headers': dict(headers)}


def get_accept_header(accept: http.Header):
    return {'accept': accept}


def get_missing_header(missing: http.Header):
    return {'missing': missing}


def get_path_params(params: http.PathParams):
    return {'params': params}


def get_request_data(data: http.RequestData):
    if isinstance(data, dict):
        data = {
            key: value if not hasattr(value, 'filename') else {
                'filename': value.filename,
                'content': value.read().decode('utf-8'),
            } for key, value in data.items()
        }
    return {'data': data}


def get_full_request_data(data: http.RequestData):
    return {'data': [
        (key, value if not hasattr(value, 'filename') else {
            'filename': value.filename,
            'content': value.read().decode('utf-8'),
        }) for key, value in data.items(multi=True)
    ]}


def return_string(data: http.RequestData) -> str:
    return '<html><body>example content</body></html>'


def return_data(data: http.RequestData) -> dict:
    return {'example': 'content'}


def return_response(data: http.RequestData) -> http.Response:
    return http.JSONResponse({'example': 'content'})


routes = [
    Route('/request/', 'GET', get_request),
    Route('/method/', 'GET', get_method),
    Route('/method/', 'POST', get_method, name='post_method'),
    Route('/scheme/', 'GET', get_scheme),
    Route('/host/', 'GET', get_host),
    Route('/port/', 'GET', get_port),
    Route('/path/', 'GET', get_path),
    Route('/query_string/', 'GET', get_query_string),
    Route('/query_params/', 'GET', get_query_params),
    Route('/page_query_param/', 'GET', get_page_query_param),
    Route('/url/', 'GET', get_url),
    Route('/body/', 'POST', get_body),
    Route('/headers/', 'GET', get_headers),
    Route('/headers/', 'POST', get_headers, name='post_headers'),
    Route('/accept_header/', 'GET', get_accept_header),
    Route('/missing_header/', 'GET', get_missing_header),
    Route('/path_params/{example}/', 'GET', get_path_params),
    Route('/full_path_params/{+example}', 'GET', get_path_params, name='full_path_params'),
    Route('/request_data/', 'POST', get_request_data),
    Route('/full_request_data/', 'POST', get_full_request_data),
    Route('/return_string/', 'GET', return_string),
    Route('/return_data/', 'GET', return_data),
    Route('/return_response/', 'GET', return_response),
]


@pytest.fixture(scope='module', params=['wsgi', 'asgi'])
def client(request):
    if request.param == 'asgi':
        app = ASyncApp(routes=routes)
    else:
        app = App(routes=routes)
    return test.TestClient(app)


def test_request(client):
    response = client.get('/request/')
    assert response.json() == {
        'method': 'GET',
        'url': 'http://testserver/request/',
        'headers': {
            'accept': '*/*',
            'accept-encoding': 'gzip, deflate',
            'connection': 'keep-alive',
            'host': 'testserver',
            'user-agent': 'testclient'
        },
        'body': ''
    }


def test_method(client):
    response = client.get('/method/')
    assert response.json() == {'method': 'GET'}
    response = client.post('/method/')
    assert response.json() == {'method': 'POST'}


def test_scheme(client):
    response = client.get('http://example.com/scheme/')
    assert response.json() == {'scheme': 'http'}
    response = client.get('https://example.com/scheme/')
    assert response.json() == {'scheme': 'https'}


def test_host(client):
    response = client.get('http://example.com/host/')
    assert response.json() == {'host': 'example.com'}


def test_port(client):
    response = client.get('http://example.com/port/')
    assert response.json() == {'port': 80}
    response = client.get('https://example.com/port/')
    assert response.json() == {'port': 443}
    response = client.get('http://example.com:123/port/')
    assert response.json() == {'port': 123}
    response = client.get('https://example.com:123/port/')
    assert response.json() == {'port': 123}


def test_path(client):
    response = client.get('/path/')
    assert response.json() == {'path': '/path/'}


def test_query_string(client):
    response = client.get('/query_string/')
    assert response.json() == {'query_string': ''}
    response = client.get('/query_string/?a=1&a=2&b=3')
    assert response.json() == {'query_string': 'a=1&a=2&b=3'}


def test_query_params(client):
    response = client.get('/query_params/')
    assert response.json() == {'query_params': {}}
    response = client.get('/query_params/?a=1&a=2&b=3')
    assert response.json() == {
        'query_params': {'a': '1', 'b': '3'}
    }


def test_single_query_param(client):
    response = client.get('/page_query_param/')
    assert response.json() == {'page': None}
    response = client.get('/page_query_param/?page=123')
    assert response.json() == {'page': '123'}
    response = client.get('/page_query_param/?page=123&page=456')
    assert response.json() == {'page': '123'}


def test_url(client):
    response = client.get('http://example.com/url/')
    assert response.json() == {
        'url': 'http://example.com/url/',
        'url.components': ['http', 'example.com', '/url/', '', '', '']
    }
    response = client.get('https://example.com/url/')
    assert response.json() == {
        'url': 'https://example.com/url/',
        'url.components': ['https', 'example.com', '/url/', '', '', '']
    }
    response = client.get('http://example.com:123/url/')
    assert response.json() == {
        'url': 'http://example.com:123/url/',
        'url.components': ['http', 'example.com:123', '/url/', '', '', '']
    }
    response = client.get('https://example.com:123/url/')
    assert response.json() == {
        'url': 'https://example.com:123/url/',
        'url.components': ['https', 'example.com:123', '/url/', '', '', '']
    }
    response = client.get('http://example.com/url/?a=1')
    assert response.json() == {
        'url': 'http://example.com/url/?a=1',
        'url.components': ['http', 'example.com', '/url/', '', 'a=1', '']
    }


def test_body(client):
    response = client.post('/body/', data="content")
    assert response.json() == {'body': 'content'}


def test_headers(client):
    response = client.get('http://example.com/headers/')
    assert response.json() == {'headers': {
        'accept': '*/*',
        'accept-encoding': 'gzip, deflate',
        'connection': 'keep-alive',
        'host': 'example.com',
        'user-agent': 'testclient'
    }}
    response = client.get('http://example.com/headers/', headers={
        'X-Example-Header': 'example'
    })
    assert response.json() == {'headers': {
        'accept': '*/*',
        'accept-encoding': 'gzip, deflate',
        'connection': 'keep-alive',
        'host': 'example.com',
        'user-agent': 'testclient',
        'x-example-header': 'example'
    }}

    response = client.post('http://example.com/headers/', data={'a': 1})
    assert response.json() == {'headers': {
        'accept': '*/*',
        'accept-encoding': 'gzip, deflate',
        'connection': 'keep-alive',
        'content-length': '3',
        'content-type': 'application/x-www-form-urlencoded',
        'host': 'example.com',
        'user-agent': 'testclient'
    }}


def test_accept_header(client):
    response = client.get('/accept_header/')
    assert response.json() == {'accept': '*/*'}


def test_missing_header(client):
    response = client.get('/missing_header/')
    assert response.json() == {'missing': None}


def test_path_params(client):
    response = client.get('/path_params/abc/')
    assert response.json() == {'params': {'example': 'abc'}}
    response = client.get('/path_params/a%20b%20c/')
    assert response.json() == {'params': {'example': 'a b c'}}
    response = client.get('/path_params/abc/def/')
    assert response.status_code == 404


def test_full_path_params(client):
    response = client.get('/full_path_params/abc/def/')
    assert response.json() == {'params': {'example': 'abc/def/'}}


@pytest.mark.parametrize('request_params,response_status,response_json', [
    # JSON
    param({'json': {'abc': 123}}, 200, {'data': {'abc': 123}}, id='valid json body'),
    param({}, 200, {'data': None}, id='empty json body'),

    # Urlencoding
    param({'data': {'abc': 123}}, 200, {'data': {'abc': '123'}}, id='valid urlencoded body'),
    param(
        {'headers': {'content-type': 'application/x-www-form-urlencoded'}}, 200, {'data': None},
        id='empty urlencoded body',
    ),

    # Misc
    param({'data': b'...', 'headers': {'content-type': 'unknown'}}, 415, None, id='unknown body type'),
    param({'data': b'...', 'headers': {'content-type': 'application/json'}}, 400, None, id='json parse failure'),
])
def test_request_data(request_params, response_status, response_json, client):
    response = client.post('/request_data/', **request_params)
    assert response.status_code == response_status
    if response_json is not None:
        assert response.json() == response_json


def test_multipart_request_data(client):
    response = client.post('/request_data/', files={'a': ('b', '123')}, data={'b': '42'})
    assert response.status_code == 200
    assert response.json() == {
        'data': {
            'a': {
                'filename': 'b',
                'content': '123',
            },
            'b': '42',
        }
    }

    response = client.post('/full_request_data/', files={'a': ('b', '123')}, data={'b': ['41', '42']})
    assert response.status_code == 200
    assert response.json() == {
        'data': [
            ['b', '41'],
            ['b', '42'],
            ['a', {
                'filename': 'b',
                'content': '123',
            }],
        ]
    }


def test_return_string(client):
    response = client.get('/return_string/')
    assert response.text == '<html><body>example content</body></html>'


def test_return_data(client):
    response = client.get('/return_data/')
    assert response.json() == {'example': 'content'}


def test_return_response(client):
    response = client.get('/return_response/')
    assert response.json() == {'example': 'content'}


def test_headers_type(client):
    h = http.Headers([('a', '123'), ('A', '456'), ('b', '789')])
    assert 'a' in h
    assert 'A' in h
    assert 'b' in h
    assert 'B' in h
    assert 'c' not in h
    assert h['a'] == '123'
    assert h.get_list('a') == ['123', '456']
    assert h.keys() == ['a', 'a', 'b']
    assert h.values() == ['123', '456', '789']
    assert h.items() == [('a', '123'), ('a', '456'), ('b', '789')]
    assert list(h) == [('a', '123'), ('a', '456'), ('b', '789')]
    assert dict(h) == {'a': '123', 'b': '789'}
    assert repr(h) == "Headers([('a', '123'), ('a', '456'), ('b', '789')])"
    assert http.Headers({'a': '123', 'b': '456'}) == http.Headers([('a', '123'), ('b', '456')])
    assert http.Headers({'a': '123', 'b': '456'}) == {'B': '456', 'a': '123'}
    assert http.Headers({'a': '123', 'b': '456'}) == [('B', '456'), ('a', '123')]
    assert {'B': '456', 'a': '123'} == http.Headers({'a': '123', 'b': '456'})
    assert [('B', '456'), ('a', '123')] == http.Headers({'a': '123', 'b': '456'})


def test_queryparams_type(client):
    q = http.QueryParams([('a', '123'), ('a', '456'), ('b', '789')])
    assert 'a' in q
    assert 'A' not in q
    assert 'c' not in q
    assert q['a'] == '123'
    assert q.get_list('a') == ['123', '456']
    assert q.keys() == ['a', 'a', 'b']
    assert q.values() == ['123', '456', '789']
    assert q.items() == [('a', '123'), ('a', '456'), ('b', '789')]
    assert list(q) == [('a', '123'), ('a', '456'), ('b', '789')]
    assert dict(q) == {'a': '123', 'b': '789'}
    assert repr(q) == "QueryParams([('a', '123'), ('a', '456'), ('b', '789')])"
    assert http.QueryParams({'a': '123', 'b': '456'}) == http.QueryParams([('a', '123'), ('b', '456')])
    assert http.QueryParams({'a': '123', 'b': '456'}) == {'b': '456', 'a': '123'}
    assert http.QueryParams({'a': '123', 'b': '456'}) == [('b', '456'), ('a', '123')]
    assert {'b': '456', 'a': '123'} == http.QueryParams({'a': '123', 'b': '456'})
    assert [('b', '456'), ('a', '123')] == http.QueryParams({'a': '123', 'b': '456'})
