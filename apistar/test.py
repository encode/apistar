import asyncio
import io
import typing
from urllib.parse import unquote, urlparse

import requests


class _HeaderDict(requests.packages.urllib3._collections.HTTPHeaderDict):
    def get_all(self, key, default):
        return self.getheaders(key)


class _MockOriginalResponse(object):
    """
    We have to jump through some hoops to present the response as if
    it was made using urllib3.
    """
    def __init__(self, headers):
        self.msg = _HeaderDict(headers)
        self.closed = False

    def isclosed(self):
        return self.closed

    def close(self):
        self.closed = True


class _WSGIAdapter(requests.adapters.HTTPAdapter):
    """
    A transport adapter for `requests` that makes requests directly to a
    WSGI app, rather than making actual HTTP requests over the network.
    """
    def __init__(self, app: typing.Callable) -> None:
        self.app = app

    def get_environ(self, request: requests.PreparedRequest) -> typing.Dict[str, typing.Any]:
        """
        Given a `requests.PreparedRequest` instance, return a WSGI environ dict.
        """
        body = request.body
        if isinstance(body, str):
            body_bytes = body.encode("utf-8")  # type: bytes
        else:
            body_bytes = body

        url_components = urlparse(request.url)
        environ = {
            'REQUEST_METHOD': request.method,
            'wsgi.url_scheme': url_components.scheme,
            'SCRIPT_NAME': '',
            'PATH_INFO': unquote(url_components.path),
            'wsgi.input': io.BytesIO(body_bytes),
        }  # type: typing.Dict[str, typing.Any]

        if url_components.query:
            environ['QUERY_STRING'] = url_components.query

        if url_components.port:
            environ['SERVER_NAME'] = url_components.hostname
            environ['SERVER_PORT'] = str(url_components.port)
        else:
            environ['HTTP_HOST'] = url_components.hostname

        for key, value in request.headers.items():
            key = key.upper().replace('-', '_')
            if key not in ('CONTENT_LENGTH', 'CONTENT_TYPE'):
                key = 'HTTP_' + key
            environ[key] = value

        return environ

    def send(self, request, *args, **kwargs):
        """
        Make an outgoing request to a WSGI application.
        """
        raw_kwargs = {}

        def start_response(wsgi_status, wsgi_headers, exc_info=None):
            if exc_info is not None:
                raise exc_info[0].with_traceback(exc_info[1], exc_info[2])
            status, _, reason = wsgi_status.partition(' ')
            raw_kwargs['status'] = int(status)
            raw_kwargs['reason'] = reason
            raw_kwargs['headers'] = wsgi_headers
            raw_kwargs['version'] = 11
            raw_kwargs['preload_content'] = False
            raw_kwargs['original_response'] = _MockOriginalResponse(wsgi_headers)

        # Make the outgoing request via WSGI.
        environ = self.get_environ(request)
        wsgi_response = self.app(environ, start_response)

        # Build the underlying urllib3.HTTPResponse
        raw_kwargs['body'] = io.BytesIO(b''.join(wsgi_response))
        raw = requests.packages.urllib3.HTTPResponse(**raw_kwargs)

        # Build the requests.Response
        return self.build_response(request, raw)


class _ASGIAdapter(requests.adapters.HTTPAdapter):
    def __init__(self, app: typing.Callable) -> None:
        self.app = app

    def send(self, request, *args, **kwargs):
        scheme, netloc, path, params, query, fragement = urlparse(request.url)
        if ':' in netloc:
            host, port = netloc.split(':', 1)
            port = int(port)
        else:
            host = netloc
            port = {'http': 80, 'https': 443}[scheme]

        # Include the 'host' header.
        if 'host' in request.headers:
            headers = []
        elif port == 80:
            headers = [[b'host', host.encode()]]
        else:
            headers = [[b'host', ('%s:%d' % (host, port)).encode()]]

        # Include other request headers.
        headers += [
            [key.encode(), value.encode()]
            for key, value in request.headers.items()
        ]

        scope = {
            'type': 'http',
            'http_version': '1.1',
            'method': request.method,
            'path': unquote(path),
            'root_path': '',
            'scheme': scheme,
            'query_string': query.encode(),
            'headers': headers,
            'client': ['testclient', 50000],
            'server': [host, port],
            'raise_exceptions': True  # Not actually part of the spec.
        }

        async def receive():
            body = request.body
            if isinstance(body, str):
                body_bytes = body.encode("utf-8")  # type: bytes
            elif body is None:
                body_bytes = b''
            else:
                body_bytes = body
            return {
                'type': 'http.request',
                'body': body_bytes,
            }

        async def send(message):
            if message['type'] == 'http.response.start':
                raw_kwargs['version'] = 11
                raw_kwargs['status'] = message['status']
                raw_kwargs['headers'] = [
                    (key.decode(), value.decode())
                    for key, value in message['headers']
                ]
                raw_kwargs['preload_content'] = False
                raw_kwargs['original_response'] = _MockOriginalResponse(raw_kwargs['headers'])
            elif message['type'] == 'http.response.body':
                raw_kwargs['body'] = io.BytesIO(message['body'])
            elif message['type'] == 'http.disconnect':
                pass
            elif message['type'] == 'http.exc_info':
                exc_info = message['exc_info']
                raise exc_info[0].with_traceback(exc_info[1], exc_info[2])
            else:
                raise Exception("Unknown ASGI message type: %s" % message['type'])

        raw_kwargs = {}
        connection = self.app(scope)

        loop = asyncio.get_event_loop()
        loop.run_until_complete(connection(receive, send))

        raw = requests.packages.urllib3.HTTPResponse(**raw_kwargs)
        return self.build_response(request, raw)


class _TestClient(requests.Session):
    def __init__(self, app: typing.Callable, scheme: str, hostname: str) -> None:
        super(_TestClient, self).__init__()
        interface = getattr(app, 'interface', None)
        if interface == 'asgi':
            adapter = _ASGIAdapter(app)
        else:
            adapter = _WSGIAdapter(app)
        self.mount('http://', adapter)
        self.mount('https://', adapter)
        self.headers.update({'User-Agent': 'testclient'})
        self.scheme = scheme
        self.hostname = hostname

    def request(self, method: str, url: str, **kwargs) -> requests.Response:  # type: ignore
        if not (url.startswith('http:') or url.startswith('https:')):
            assert url.startswith('/'), (
                "TestClient expected either "
                "an absolute URL starting 'http:' / 'https:', "
                "or a relative URL starting with '/'. URL was '%s'." % url
            )
            url = '%s://%s%s' % (self.scheme, self.hostname, url)
        return super().request(method, url, **kwargs)


def TestClient(app: typing.Callable, scheme: str='http', hostname: str='testserver') -> _TestClient:
    """
    We have to work around py.test discovery attempting to pick up
    the `TestClient` class, by declaring this as a function.
    """
    return _TestClient(app, scheme, hostname)
