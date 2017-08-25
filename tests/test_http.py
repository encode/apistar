import pytest

from apistar import Route, TestClient, http
from apistar.frameworks.asyncio import ASyncIOApp
from apistar.frameworks.wsgi import WSGIApp


def to_native(obj):  # pragma: nocover  (Some cases only included for completeness)
    if isinstance(obj, dict):
        return {key: to_native(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [to_native(value) for value in obj]
    elif hasattr(obj, 'read'):
        content = obj.read()
        if isinstance(content, bytes):
            content = content.decode('utf-8')
        return content
    elif hasattr(obj, '__dict__'):
        return str(obj)
    return obj


# HTTP Components as parameters

def get_request(request: http.Request) -> http.Response:
    return http.Response({
        'method': request.method,
        'url': request.url,
        'headers': dict(request.headers),
        'body': request.body.decode('utf-8')
    })


def get_method(method: http.Method) -> http.Response:
    return http.Response({'method': method})


def get_scheme(scheme: http.Scheme) -> http.Response:
    return http.Response({'scheme': scheme})


def get_host(host: http.Host) -> http.Response:
    return http.Response({'host': host})


def get_port(port: http.Port) -> http.Response:
    return http.Response({'port': port})


def get_path(path: http.Path) -> http.Response:
    return http.Response({'path': path})


def get_query_string(query_string: http.QueryString) -> http.Response:
    return http.Response({'query_string': query_string})


def get_query_params(query_string: http.QueryString, query_params: http.QueryParams) -> http.Response:
    return http.Response({'query_params': dict(query_params)})


def get_page_query_param(page: http.QueryParam) -> http.Response:
    return http.Response({'page': page})


def get_untyped_page_query_param(page) -> http.Response:
    return http.Response({'page': page})


def get_scalar_page_query_param(page: int) -> http.Response:
    return http.Response({'page': page})


def get_url(url: http.URL) -> http.Response:
    return http.Response({'url': url, 'url.components': url.components})


def get_body(body: http.Body) -> http.Response:
    return http.Response({'body': body.decode('utf-8')})


def get_data(data: http.RequestData) -> http.Response:
    return http.Response({'data': to_native(data)})


def get_headers(headers: http.Headers) -> http.Response:
    return http.Response({'headers': dict(headers)})


def get_accept_header(accept: http.Header) -> http.Response:
    return http.Response({'accept': accept})


# Different response types

def binary_response():
    return b'<html><h1>Hello, world</h1></html>'


def text_response():
    return '<html><h1>Hello, world</h1></html>'


def data_response():
    return {'hello': 'world'}


def empty_response():
    return None


def unknown_status_code() -> http.Response:
    data = {'hello': 'world'}
    return http.Response(data, status=600)


def response_headers() -> http.Response:
    data = {'hello': 'world'}
    headers = {'Content-Language': 'de'}
    return http.Response(data, headers=headers)


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
    Route('/untyped_page_query_param/', 'GET', get_untyped_page_query_param),
    Route('/scalar_page_query_param/', 'GET', get_scalar_page_query_param),
    Route('/url/', 'GET', get_url),
    Route('/body/', 'POST', get_body),
    Route('/data/', 'POST', get_data),
    Route('/headers/', 'GET', get_headers),
    Route('/headers/', 'POST', get_headers, name='post_headers'),
    Route('/accept_header/', 'GET', get_accept_header),
    Route('/binary/', 'GET', binary_response),
    Route('/text/', 'GET', text_response),
    Route('/data/', 'GET', data_response),
    Route('/empty/', 'GET', empty_response),
    Route('/unknown_status_code/', 'GET', unknown_status_code),
    Route('/response_headers/', 'GET', response_headers),
]

wsgi_app = WSGIApp(routes=routes)
wsgi_client = TestClient(wsgi_app)

async_app = ASyncIOApp(routes=routes)
async_client = TestClient(async_app)


@pytest.mark.parametrize('client', [wsgi_client, async_client])
def test_request(client):
    response = client.get('http://example.com/request/')
    assert response.json() == {
        'method': 'GET',
        'url': 'http://example.com/request/',
        'headers': {
            'accept': '*/*',
            'accept-encoding': 'gzip, deflate',
            'connection': 'keep-alive',
            'host': 'example.com',
            'user-agent': 'testclient'
        },
        'body': ''
    }


@pytest.mark.parametrize('client', [wsgi_client, async_client])
def test_method(client):
    response = client.get('http://example.com/method/')
    assert response.json() == {'method': 'GET'}
    response = client.post('http://example.com/method/')
    assert response.json() == {'method': 'POST'}


@pytest.mark.parametrize('client', [wsgi_client, async_client])
def test_scheme(client):
    response = client.get('http://example.com/scheme/')
    assert response.json() == {'scheme': 'http'}
    response = client.get('https://example.com/scheme/')
    assert response.json() == {'scheme': 'https'}


@pytest.mark.parametrize('client', [wsgi_client, async_client])
def test_host(client):
    response = client.get('http://example.com/host/')
    assert response.json() == {'host': 'example.com'}


@pytest.mark.parametrize('client', [wsgi_client, async_client])
def test_port(client):
    response = client.get('http://example.com/port/')
    assert response.json() == {'port': 80}
    response = client.get('https://example.com/port/')
    assert response.json() == {'port': 443}
    response = client.get('http://example.com:123/port/')
    assert response.json() == {'port': 123}
    response = client.get('https://example.com:123/port/')
    assert response.json() == {'port': 123}


@pytest.mark.parametrize('client', [wsgi_client, async_client])
def test_path(client):
    response = client.get('http://example.com/path/')
    assert response.json() == {'path': '/path/'}


@pytest.mark.parametrize('client', [wsgi_client, async_client])
def test_query_string(client):
    response = client.get('http://example.com/query_string/')
    assert response.json() == {'query_string': ''}
    response = client.get('http://example.com/query_string/?a=1&a=2&b=3')
    assert response.json() == {'query_string': 'a=1&a=2&b=3'}


@pytest.mark.parametrize('client', [wsgi_client, async_client])
def test_query_params(client):
    response = client.get('http://example.com/query_params/')
    assert response.json() == {'query_params': {}}
    response = client.get('http://example.com/query_params/?a=1&a=2&b=3')
    assert response.json() == {
        'query_params': {'a': '1', 'b': '3'}
    }


@pytest.mark.parametrize('client', [wsgi_client, async_client])
def test_single_query_param(client):
    """
    Tests a route where the `page` arg is annotated as a QueryParam
    """
    response = client.get('http://example.com/page_query_param/')
    assert response.json() == {'page': None}
    response = client.get('http://example.com/page_query_param/?page=123')
    assert response.json() == {'page': '123'}
    response = client.get(
        'http://example.com/page_query_param/?page=123&page=456')
    assert response.json() == {'page': '123'}


@pytest.mark.parametrize('client', [wsgi_client, async_client])
def test_single_untyped_query_param(client):
    """
    Tests a route where the `page` arg is not annotated
    """
    response = client.get('http://example.com/untyped_page_query_param/')
    assert response.json() == {'page': None}
    response = client.get(
        'http://example.com/untyped_page_query_param/?page=123')
    assert response.json() == {'page': '123'}
    response = client.get(
        'http://example.com/untyped_page_query_param/?page=123&page=456')
    assert response.json() == {'page': '123'}


@pytest.mark.parametrize('client', [wsgi_client, async_client])
def test_single_scalar_query_param(client):
    """
    Tests a route where the `page` arg is annotated as an int
    """
    response = client.get('http://example.com/scalar_page_query_param/')
    assert response.json() == {'page': None}
    response = client.get(
        'http://example.com/scalar_page_query_param/?page=123')
    assert response.json() == {'page': 123}
    response = client.get(
        'http://example.com/scalar_page_query_param/?page=123&page=456')
    assert response.json() == {'page': 123}


@pytest.mark.parametrize('client', [wsgi_client, async_client])
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


@pytest.mark.parametrize('client', [wsgi_client, async_client])
def test_body(client):
    response = client.post('http://example.com/body/', data="content")
    assert response.json() == {'body': 'content'}


@pytest.mark.parametrize('client', [wsgi_client, async_client])
def test_data(client):
    response = client.post('http://example.com/data/', json={"hello": 123})
    assert response.json() == {'data': {'hello': 123}}

    response = client.post('http://example.com/data/')
    assert response.json() == {'data': None}

    response = client.post('http://example.com/data/', data={'abc': 123})
    assert response.json() == {'data': {'abc': '123'}}

    csv_file = ('report.csv', '1,2,3\n4,5,6\n')
    response = client.post('http://example.com/data/', files={'file': csv_file})
    assert response.json() == {'data': {'file': '1,2,3\n4,5,6\n'}}

    response = client.post('http://example.com/data/', headers={b'content-type': b'unknown'})
    assert response.status_code == 415


@pytest.mark.parametrize('client', [wsgi_client, async_client])
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


@pytest.mark.parametrize('client', [wsgi_client, async_client])
def test_accept_header(client):
    response = client.get('http://example.com/accept_header/')
    assert response.json() == {'accept': '*/*'}


@pytest.mark.parametrize('client', [wsgi_client, async_client])
def test_binary_response(client):
    response = client.get('/binary/')
    assert response.text == '<html><h1>Hello, world</h1></html>'
    assert response.headers['Content-Type'] == 'text/html; charset=utf-8'


@pytest.mark.parametrize('client', [wsgi_client, async_client])
def test_text_response(client):
    response = client.get('/text/')
    assert response.text == '<html><h1>Hello, world</h1></html>'
    assert response.headers['Content-Type'] == 'text/html; charset=utf-8'


@pytest.mark.parametrize('client', [wsgi_client, async_client])
def test_data_response(client):
    response = client.get('/data/')
    assert response.json() == {'hello': 'world'}
    assert response.headers['Content-Type'] == 'application/json'


@pytest.mark.parametrize('client', [wsgi_client, async_client])
def test_empty_response(client):
    response = client.get('/empty/')
    assert response.status_code == 204
    assert response.text == ''


@pytest.mark.parametrize('client', [wsgi_client, async_client])
def test_unknown_status_code(client):
    response = client.get('/unknown_status_code/')
    assert response.status_code == 600
    assert response.json() == {'hello': 'world'}
    assert response.headers['Content-Type'] == 'application/json'


@pytest.mark.parametrize('client', [wsgi_client, async_client])
def test_response_headers(client):
    response = client.get('/response_headers/')
    assert response.headers['Content-Language'] == 'de'


def test_headers_type():
    h = http.Headers([('a', '123'), ('A', '456'), ('b', '789')])
    assert 'a' in h
    assert 'A' in h
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


def test_queryparams_type():
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
