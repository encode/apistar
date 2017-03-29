from apistar import App, Route
from apistar.test import TestClient
from apistar.components import http


def get_method(method: http.Method) -> http.Response:
    return http.Response({'method': method})


def get_scheme(scheme: http.Scheme) -> http.Response:
    return http.Response({'scheme': scheme})


def get_host(host: http.Host) -> http.Response:
    return http.Response({'host': host})


def get_port(port: http.Port) -> http.Response:
    return http.Response({'port': port})


def get_root_path(root_path: http.RootPath) -> http.Response:
    return http.Response({'root_path': root_path})


def get_path(path: http.Path) -> http.Response:
    return http.Response({'path': path})


def get_query_string(query_string: http.QueryString) -> http.Response:
    return http.Response({'query_string': query_string})


def get_query_params(query_params: http.QueryParams) -> http.Response:
    return http.Response({'query_params': query_params.to_dict(flat=False)})


def get_page_query_param(page: http.NamedQueryParam) -> http.Response:
    return http.Response({'page': page})


def get_url(url: http.URL) -> http.Response:
    return http.Response({'url': url})


def get_headers(headers: http.Headers) -> http.Response:
    return http.Response({'headers': dict(headers)})


def get_accept_header(accept: http.NamedHeader) -> http.Response:
    return http.Response({'accept': accept})


def get_request(request: http.Request) -> http.Response:
    return http.Response({
        'method': request.method,
        'url': request.url,
        'headers': dict(request.headers)
    })


app = App(routes=[
    Route('/method/', 'get', get_method),
    Route('/method/', 'post', get_method),
    Route('/scheme/', 'get', get_scheme),
    Route('/host/', 'get', get_host),
    Route('/port/', 'get', get_port),
    Route('/root_path/', 'get', get_root_path),
    Route('/path/', 'get', get_path),
    Route('/query_string/', 'get', get_query_string),
    Route('/query_params/', 'get', get_query_params),
    Route('/page_query_param/', 'get', get_page_query_param),
    Route('/url/', 'get', get_url),
    Route('/headers/', 'get', get_headers),
    Route('/accept_header/', 'get', get_accept_header),
    Route('/request/', 'get', get_request),
])


client = TestClient(app)


def test_method():
    response = client.get('http://example.com/method/')
    assert response.json() == {'method': 'GET'}
    response = client.post('http://example.com/method/')
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


def test_root_path():
    client = test.RequestsClient(app, root_path='/mount_point/')
    response = client.get('http://example.com/mount_point/root_path/')
    assert response.json() == {
        'root_path': '/mount_point'
    }
    response = client.get('http://example.com/mount_point/path/')
    assert response.json() == {
        'path': '/path/'
    }
    response = client.get('http://example.com/mount_point/path/')
    assert response.json() == {
        'url': 'http://example.com/mount_point/root_path/'
    }


def test_root_path():
    response = client.get('http://example.com/root_path/')
    assert response.json() == {'root_path': ''}


def test_path():
    response = client.get('http://example.com/path/')
    assert response.json() == {'path': '/path/'}


def test_query_string():
    response = client.get('http://example.com/query_string/')
    assert response.json() == {'query_string': ''}
    response = client.get('http://example.com/query_string/?a=1&a=2&b=3')
    assert response.json() == {'query_string': 'a=1&a=2&b=3'}


def test_query_params():
    response = client.get('http://example.com/query_params/')
    assert response.json() == {'query_params': {}}
    response = client.get('http://example.com/query_params/?a=1&a=2&b=3')
    assert response.json() == {
        'query_params': {'a': ['1', '2'], 'b': ['3']}
    }


def test_single_query_param():
    response = client.get('http://example.com/page_query_param/')
    assert response.json() == {'page': None}
    response = client.get('http://example.com/page_query_param/?page=123')
    assert response.json() == {'page': '123'}
    response = client.get('http://example.com/page_query_param/?page=123&page=456')
    assert response.json() == {'page': '123'}


def test_url():
    response = client.get('http://example.com/url/')
    assert response.json() == {'url': 'http://example.com/url/'}
    response = client.get('https://example.com/url/')
    assert response.json() == {'url': 'https://example.com/url/'}
    response = client.get('http://example.com:123/url/')
    assert response.json() == {'url': 'http://example.com:123/url/'}
    response = client.get('https://example.com:123/url/')
    assert response.json() == {'url': 'https://example.com:123/url/'}
    response = client.get('http://example.com/url/?a=1')
    assert response.json() == {'url': 'http://example.com/url/?a=1'}


def test_headers():
    response = client.get('http://example.com/headers/')
    assert response.json() == {'headers': {
        'Accept': '*/*',
        'Accept-Encoding': 'gzip, deflate',
        'Connection': 'keep-alive',
        'Host': 'example.com',
        'User-Agent': 'requests_client'
    }}
    response = client.get('http://example.com/headers/', headers={
        'X-Example-Header': 'example'
    })
    assert response.json() == {'headers': {
        'Accept': '*/*',
        'Accept-Encoding': 'gzip, deflate',
        'Connection': 'keep-alive',
        'Host': 'example.com',
        'User-Agent': 'requests_client',
        'X-Example-Header': 'example'
    }}


def test_accept_header():
    response = client.get('http://example.com/accept_header/')
    assert response.json() == {'accept': '*/*'}


def test_request():
    response = client.get('http://example.com/request/')
    assert response.json() == {
        'method': 'GET',
        'url': 'http://example.com/request/',
        'headers': {
            'Accept': '*/*',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Host': 'example.com',
            'User-Agent': 'requests_client'
        }
    }
