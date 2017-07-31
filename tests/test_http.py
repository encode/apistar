from apistar import App, Route, TestClient, http


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


def get_query_params(query_params: http.QueryParams) -> http.Response:
    return http.Response({'query_params': query_params.to_dict(flat=False)})


def get_page_query_param(page: http.QueryParam) -> http.Response:
    return http.Response({'page': page})


def get_url(url: http.URL) -> http.Response:
    return http.Response({'url': url})


def get_body(body: http.Body) -> http.Response:
    return http.Response({'body': body.decode('utf-8')})


def get_data(data: http.RequestData) -> http.Response:
    return http.Response({'data': to_native(data)})


# def get_field(field: http.RequestField) -> http.Response:
#     return http.Response({'field': to_native(field)})


def get_headers(headers: http.Headers) -> http.Response:
    return http.Response({'headers': dict(headers)})


def get_accept_header(accept: http.Header) -> http.Response:
    return http.Response({'accept': accept})


# def get_request(request: http.Request) -> http.Response:
#     return http.Response({
#         'method': request.method,
#         'url': request.url,
#         'headers': dict(request.headers)
#     })


app = App(routes=[
    Route('/method/', 'GET', get_method),
    Route('/method/', 'POST', get_method),
    Route('/scheme/', 'GET', get_scheme),
    Route('/host/', 'GET', get_host),
    Route('/port/', 'GET', get_port),
    Route('/path/', 'GET', get_path),
    Route('/query_string/', 'GET', get_query_string),
    Route('/query_params/', 'GET', get_query_params),
    Route('/page_query_param/', 'GET', get_page_query_param),
    Route('/url/', 'GET', get_url),
    Route('/body/', 'POST', get_body),
    Route('/data/', 'POST', get_data),
    # Route('/field/', 'POST', get_field),
    Route('/headers/', 'GET', get_headers),
    Route('/accept_header/', 'GET', get_accept_header),
    # Route('/request/', 'GET', get_request),
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


def test_body():
    response = client.post('http://example.com/body/', data="content")
    assert response.json() == {'body': 'content'}


def test_data():
    response = client.post('http://example.com/data/', json={"hello": 123})
    assert response.json() == {'data': {'hello': 123}}

    response = client.post('http://example.com/data/')
    assert response.json() == {'data': None}

    response = client.post('http://example.com/data/', data={'abc': 123})
    assert response.json() == {'data': {'abc': '123'}}

    csv_file = ('report.csv', '1,2,3\n4,5,6\n')
    response = client.post('http://example.com/data/', files={'file': csv_file})
    assert response.json() == {'data': {'file': '1,2,3\n4,5,6\n'}}

    response = client.post('http://example.com/data/', headers={'content-type': 'unknown'})
    assert response.status_code == 415


# def test_field():
#     response = client.post('http://example.com/field/', json={"field": 123})
#     assert response.json() == {'field': 123}
#
#     response = client.post('http://example.com/field/', data={'field': 123})
#     assert response.json() == {'field': '123'}
#
#     csv_file = ('report.csv', '1,2,3\n4,5,6\n')
#     response = client.post('http://example.com/field/', files={'field': csv_file})
#     assert response.json() == {'field': '1,2,3\n4,5,6\n'}


def test_headers():
    response = client.get('http://example.com/headers/')
    assert response.json() == {'headers': {
        'Accept': '*/*',
        'Accept-Encoding': 'gzip, deflate',
        'Connection': 'keep-alive',
        'Host': 'example.com',
        'User-Agent': 'testclient'
    }}
    response = client.get('http://example.com/headers/', headers={
        'X-Example-Header': 'example'
    })
    assert response.json() == {'headers': {
        'Accept': '*/*',
        'Accept-Encoding': 'gzip, deflate',
        'Connection': 'keep-alive',
        'Host': 'example.com',
        'User-Agent': 'testclient',
        'X-Example-Header': 'example'
    }}


def test_accept_header():
    response = client.get('http://example.com/accept_header/')
    assert response.json() == {'accept': '*/*'}


# def test_request():
#     response = client.get('http://example.com/request/')
#     assert response.json() == {
#         'method': 'GET',
#         'url': 'http://example.com/request/',
#         'headers': {
#             'Accept': '*/*',
#             'Accept-Encoding': 'gzip, deflate',
#             'Connection': 'keep-alive',
#             'Host': 'example.com',
#             'User-Agent': 'requests_client'
#         }
#     }


# Test reponse types

def binary_response():
    return b'<html><h1>Hello, world</h1></html>'


def text_response():
    return '<html><h1>Hello, world</h1></html>'


def data_response():
    return {'hello': 'world'}


def empty_response():
    return b''


def unknown_status_code() -> http.Response:
    data = {'hello': 'world'}
    return http.Response(data, status=600)


def dict_headers() -> http.Response:
    data = {'hello': 'world'}
    headers = {'Content-Language': 'de'}
    return http.Response(data, headers=headers)


def list_headers() -> http.Response:
    data = {'hello': 'world'}
    headers = [('Content-Language', 'de')]
    return http.Response(data, headers=headers)


def object_headers() -> http.Response:
    data = {'hello': 'world'}
    headers = http.Headers({'Content-Language': 'de'})
    return http.Response(data, headers=headers)


def test_binary_response():
    app = App(routes=[Route('/', 'GET', binary_response)])
    client = TestClient(app)
    response = client.get('/')
    assert response.text == '<html><h1>Hello, world</h1></html>'
    assert response.headers['Content-Type'] == 'text/html; charset=utf-8'


def test_text_response():
    app = App(routes=[Route('/', 'GET', text_response)])
    client = TestClient(app)
    response = client.get('/')
    assert response.text == '<html><h1>Hello, world</h1></html>'
    assert response.headers['Content-Type'] == 'text/html; charset=utf-8'


def test_data_response():
    app = App(routes=[Route('/', 'GET', data_response)])
    client = TestClient(app)
    response = client.get('/')
    assert response.json() == {'hello': 'world'}
    assert response.headers['Content-Type'] == 'application/json'


def test_empty_response():
    app = App(routes=[Route('/', 'GET', empty_response)])
    client = TestClient(app)
    response = client.get('/')
    assert response.status_code == 204
    assert response.text == ''


def test_unknown_status_code():
    app = App(routes=[Route('/', 'GET', unknown_status_code)])
    client = TestClient(app)
    response = client.get('/')
    assert response.status_code == 600
    assert response.json() == {'hello': 'world'}
    assert response.headers['Content-Type'] == 'application/json'


def test_dict_headers():
    app = App(routes=[Route('/', 'GET', dict_headers)])
    client = TestClient(app)
    response = client.get('/')
    assert response.headers['Content-Language'] == 'de'


def test_list_headers():
    app = App(routes=[Route('/', 'GET', list_headers)])
    client = TestClient(app)
    response = client.get('/')
    assert response.headers['Content-Language'] == 'de'


def test_object_headers():
    app = App(routes=[Route('/', 'GET', object_headers)])
    client = TestClient(app)
    response = client.get('/')
    assert response.headers['Content-Language'] == 'de'
