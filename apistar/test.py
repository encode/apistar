import io
from typing import Callable, Dict, Mapping, Optional, Union  # noqa
from urllib.parse import unquote, urlparse

import requests
from click.testing import CliRunner

from apistar.cli import get_current_app


class WSGIAdapter(requests.adapters.HTTPAdapter):
    """
    A transport adapter for `requests` that makes requests directly to a
    WSGI app, rather than making actual HTTP requests over the network.
    """
    def __init__(self, wsgi_app: Callable, root_path: str=None,
                 raise_500_exc: bool=True) -> None:
        self.wsgi_app = wsgi_app
        self.root_path = ('/' + root_path.strip('/')) if root_path else ''
        self.raise_500_exc = raise_500_exc

    def get_environ(self, request: requests.PreparedRequest) -> Mapping:
        """
        Given a `requests.PreparedRequest` instance, return a WSGI environ dict.
        """
        body = request.body
        if isinstance(body, str):
            body_bytes = body.encode("utf-8")  # type: Optional[bytes]
        else:
            body_bytes = body

        url_components = urlparse(request.url)
        environ = {
            'REQUEST_METHOD': request.method,
            'wsgi.url_scheme': url_components.scheme,
            'SCRIPT_NAME': self.root_path,
            'PATH_INFO': unquote(url_components.path),
            'wsgi.input': io.BytesIO(body_bytes),
            'APISTAR_RAISE_500_EXC': self.raise_500_exc
        }  # type: Dict[str, Union[bool, str, bytes, io.BytesIO]]

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

        def start_response(wsgi_status, wsgi_headers):
            status, _, reason = wsgi_status.partition(' ')
            raw_kwargs['status'] = int(status)
            raw_kwargs['reason'] = reason
            raw_kwargs['headers'] = wsgi_headers
            raw_kwargs['version'] = 11
            raw_kwargs['preload_content'] = False
            raw_kwargs['original_response'] = None

        # Make the outgoing request via WSGI.
        environ = self.get_environ(request)
        wsgi_response = self.wsgi_app(environ, start_response)

        # Build the underlying urllib3.HTTPResponse
        raw_kwargs['body'] = io.BytesIO(b''.join(wsgi_response))
        raw = requests.packages.urllib3.HTTPResponse(**raw_kwargs)

        # Build the requests.Response
        return self.build_response(request, raw)


class _TestClient(requests.Session):
    def __init__(self, app=None, root_path=None, raise_500_exc=True, hostname='testserver'):
        super(_TestClient, self).__init__()
        if app is None:
            app = get_current_app()

        adapter = WSGIAdapter(app.wsgi, root_path=root_path, raise_500_exc=raise_500_exc)
        self.mount('http://', adapter)
        self.mount('https://', adapter)
        self.headers.update({'User-Agent': 'requests_client'})
        self.hostname = hostname

    def request(self, method, url, **kwargs):
        if not (url.startswith('http:') or url.startswith('https:')):
            assert url.startswith('/'), (
                "TestClient expected either "
                "an absolute URL starting 'http:' / 'https:', "
                "or a relative URL starting with '/'. URL was '%s'." % url
            )
            url = 'http://' + self.hostname + url
        return super().request(method, url, **kwargs)


def TestClient(*args, **kwargs) -> _TestClient:
    """
    We have to work around py.test discovery attempting to pick up
    the `TestClient` class, by declaring this as a function.
    """
    return _TestClient(*args, **kwargs)


class CommandLineRunner(CliRunner):
    def __init__(self, app):
        self.click_client = app.click
        super(CommandLineRunner, self).__init__()

    def invoke(self, *args, **kwargs):
        args = [self.click_client] + list(args)
        return super(CommandLineRunner, self).invoke(*args, **kwargs)
