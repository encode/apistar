from apistar import http, test
from apistar.document import Document, Link
from apistar.server.app import App

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


def get_url(url: http.URL) -> http.Response:
    return http.Response({'url': url, 'url.components': url.components})


def get_body(body: http.Body) -> http.Response:
    return http.Response({'body': body.decode('utf-8')})


def get_headers(headers: http.Headers) -> http.Response:
    return http.Response({'headers': dict(headers)})


def get_accept_header(accept: http.Header) -> http.Response:
    return http.Response({'accept': accept})


def get_path_params(params: http.PathParams) -> http.Response:
    return http.Response({'params': params})


def get_request_data(data: http.RequestData) -> http.Response:
    return http.Response({'data': data})


doc = Document([
    Link('/request/', 'GET', get_request),
    Link('/method/', 'GET', get_method),
    Link('/method/', 'POST', get_method, name='post_method'),
    Link('/scheme/', 'GET', get_scheme),
    Link('/host/', 'GET', get_host),
    Link('/port/', 'GET', get_port),
    Link('/path/', 'GET', get_path),
    Link('/query_string/', 'GET', get_query_string),
    Link('/query_params/', 'GET', get_query_params),
    Link('/page_query_param/', 'GET', get_page_query_param),
    Link('/url/', 'GET', get_url),
    Link('/body/', 'POST', get_body),
    Link('/headers/', 'GET', get_headers),
    Link('/headers/', 'POST', get_headers, name='post_headers'),
    Link('/accept_header/', 'GET', get_accept_header),
    Link('/path_params/{example}/', 'GET', get_path_params),
    Link('/full_path_params/{+example}', 'GET', get_path_params, name='full_path_params'),
    Link('/request_data/', 'POST', get_request_data),
])

app = App(doc)
client = test.TestClient(app)


def test_request():
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


def test_method():
    response = client.get('/method/')
    assert response.json() == {'method': 'GET'}
    response = client.post('/method/')
    assert response.json() == {'method': 'POST'}


def test_scheme():
    response = client.get('http://example.com/scheme/')
    assert response.json() == {'scheme': 'http'}
    response = client.get('https://example.com/scheme/')
    assert response.json() == {'scheme': 'https'}


def test_host():
    response = client.get('http://example.com/host/')
    assert response.json() == {'host': 'example.com'}


def test_port():
    response = client.get('http://example.com/port/')
    assert response.json() == {'port': 80}
    response = client.get('https://example.com/port/')
    assert response.json() == {'port': 443}
    response = client.get('http://example.com:123/port/')
    assert response.json() == {'port': 123}
    response = client.get('https://example.com:123/port/')
    assert response.json() == {'port': 123}


def test_path():
    response = client.get('/path/')
    assert response.json() == {'path': '/path/'}


def test_query_string():
    response = client.get('/query_string/')
    assert response.json() == {'query_string': ''}
    response = client.get('/query_string/?a=1&a=2&b=3')
    assert response.json() == {'query_string': 'a=1&a=2&b=3'}


def test_query_params():
    response = client.get('/query_params/')
    assert response.json() == {'query_params': {}}
    response = client.get('/query_params/?a=1&a=2&b=3')
    assert response.json() == {
        'query_params': {'a': '1', 'b': '3'}
    }


def test_single_query_param():
    response = client.get('/page_query_param/')
    assert response.json() == {'page': None}
    response = client.get('/page_query_param/?page=123')
    assert response.json() == {'page': '123'}
    response = client.get('/page_query_param/?page=123&page=456')
    assert response.json() == {'page': '123'}


def test_url():
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


def test_body():
    response = client.post('/body/', data="content")
    assert response.json() == {'body': 'content'}


def test_headers():
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


def test_accept_header():
    response = client.get('/accept_header/')
    assert response.json() == {'accept': '*/*'}


def test_path_params():
    response = client.get('/path_params/abc/')
    assert response.json() == {'params': {'example': 'abc'}}
    response = client.get('/path_params/a%20b%20c/')
    assert response.json() == {'params': {'example': 'a b c'}}
    response = client.get('/path_params/abc/def/')
    assert response.status_code == 404


def test_full_path_params():
    response = client.get('/full_path_params/abc/def/')
    assert response.json() == {'params': {'example': 'abc/def/'}}


def test_request_data():
    response = client.post('/request_data/', json={'abc': 123})
    assert response.json() == {'data': {'abc': 123}}
    response = client.post('/request_data/')
    assert response.json() == {'data': None}
    response = client.post('/request_data/', data=b'...', headers={'content-type': 'unknown'})
    assert response.status_code == 415
    response = client.post('/request_data/', data=b'...', headers={'content-type': 'application/json'})
    assert response.status_code == 400


def test_headers_type():
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
