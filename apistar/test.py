import asyncio
import io
import typing
from http import HTTPStatus
from urllib.parse import unquote, urlparse

import requests

from apistar.interfaces import App


def _get_reason_phrase(status_code: int) -> str:
    try:
        return HTTPStatus(status_code).phrase
    except ValueError:
        return ''


def _coerce_to_str(item: typing.Union[str, bytes]):
    if isinstance(item, bytes):
        return item.decode()
    return item


def _coerce_to_bytes(item: typing.Union[str, bytes]):
    if isinstance(item, str):
        return item.encode()
    return item


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
            environ[key] = _coerce_to_str(value)

        return environ

    def send(self, request, *args, **kwargs):
        """
        Make an outgoing request to a WSGI application.
        """
        raw_kwargs = {}

        def start_response(wsgi_status, wsgi_headers):
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


class _MockReplyChannel():
    def __init__(self):
        self.status = None
        self.headers = None
        self.body = b''

    async def send(self, message):
        if 'status' in message:
            self.status = message['status']
        if 'headers' in message:
            self.headers = message['headers']
        if 'content' in message:
            self.body += message['content']


class _UMIAdapter(requests.adapters.HTTPAdapter):
    """
    A transport adapter for `requests` that makes requests directly to a
    asyncio app, rather than making actual HTTP requests over the network.
    """
    def __init__(self, app: typing.Callable) -> None:
        self.app = app

    def get_message(self, request: requests.PreparedRequest) -> typing.Dict[str, typing.Any]:
        """
        Given a `requests.PreparedRequest` instance, return a WSGI environ dict.
        """
        body = request.body
        if isinstance(body, str):
            body_bytes = body.encode("utf-8")  # type: bytes
        else:
            body_bytes = body

        url_components = urlparse(request.url)
        message = {
            'method': request.method,
            'scheme': url_components.scheme,
            'path': unquote(url_components.path),
            'body': body_bytes,
            'query_string': url_components.query.encode()
        }  # type: typing.Dict[str, typing.Any]

        if url_components.port:
            message['server'] = [
                url_components.hostname,
                url_components.port
            ]
        else:
            message['server'] = [
                url_components.hostname,
                443 if (url_components.scheme == 'https') else 80
            ]

        message['headers'] = [
            [b'host', url_components.hostname.encode()]
        ] + [
            [_coerce_to_bytes(key), _coerce_to_bytes(value)]
            for key, value in request.headers.items()
        ]

        return message

    def send(self, request, *args, **kwargs):
        """
        Make an outgoing request to a WSGI application.
        """
        # Make the outgoing request via WSGI.
        reply = _MockReplyChannel()
        message = self.get_message(request)
        channels = {'reply': reply}

        task = self.app(message, channels)
        loop = asyncio.get_event_loop()
        loop.run_until_complete(task)

        status = reply.status
        headers = reply.headers
        body = reply.body

        assert status is not None
        assert headers is not None

        string_headers = [
            (key.decode(), value.decode())
            for key, value in headers
        ]

        raw_kwargs = {
            'status': status,
            'reason': _get_reason_phrase(status),
            'headers': string_headers,
            'version': 11,
            'preload_content': False,
            'original_response': _MockOriginalResponse(string_headers),
            'body': io.BytesIO(body)
        }

        # Build the underlying urllib3.HTTPResponse
        raw = requests.packages.urllib3.HTTPResponse(**raw_kwargs)

        # Build the requests.Response
        return self.build_response(request, raw)


class _TestClient(requests.Session):
    def __init__(self, app: App, scheme: str, hostname: str) -> None:
        super(_TestClient, self).__init__()
        app_callable = typing.cast(typing.Callable, app)
        if asyncio.iscoroutinefunction(getattr(app, '__call__')):
            adapter = _UMIAdapter(app_callable)  # type: requests.adapters.HTTPAdapter
        else:
            adapter = _WSGIAdapter(app_callable)
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


def TestClient(app: App, scheme: str='http', hostname: str='testserver') -> _TestClient:
    """
    We have to work around py.test discovery attempting to pick up
    the `TestClient` class, by declaring this as a function.
    """
    return _TestClient(app, scheme, hostname)
