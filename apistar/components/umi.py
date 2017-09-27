import io
import typing

import werkzeug
from werkzeug.http import parse_options_header

from apistar import Settings, exceptions, http, parsers
from apistar.authentication import Unauthenticated
from apistar.interfaces import Injector
from apistar.types import Handler, ParamName, UMIChannels, UMIMessage


def get_method(message: UMIMessage):
    return message['method'].upper()


def get_url(message: UMIMessage):
    scheme = message['scheme']
    host, port = message['server']
    path = message['path']

    if (scheme == 'http' and port != 80) or (scheme == 'https' and port != 443):
        url = '%s://%s:%s%s' % (scheme, host, port, path)
    else:
        url = '%s://%s%s' % (scheme, host, path)

    query_string = message['query_string']
    if query_string:
        url += '?' + query_string.decode()

    return http.URL(url)


def get_scheme(message: UMIMessage):
    return message['scheme']


def get_host(message: UMIMessage):
    return message['server'][0]


def get_port(message: UMIMessage):
    return message['server'][1]


def get_path(message: UMIMessage):
    return message['path']


def get_querystring(message: UMIMessage):
    return message['query_string'].decode()


def get_queryparams(message: UMIMessage) -> http.QueryParams:
    return werkzeug.urls.url_decode(
        message['query_string'],
        cls=http.QueryParams
    )


def get_queryparam(name: ParamName, queryparams: http.QueryParams):
    return queryparams.get(name)


def get_headers(message: UMIMessage) -> http.Headers:
    return http.Headers([
        (key.decode(), value.decode())
        for key, value in message['headers']
    ])


def get_header(name: ParamName, headers: http.Headers):
    return headers.get(name.replace('_', '-'))


async def get_body(message: UMIMessage, channels: UMIChannels):
    body = message.get('body', b'')
    if 'body' in channels:  # pragma: nocover
        while True:
            message_chunk = await channels['body'].receive()
            body += message_chunk['content']
            if not message_chunk.get('more_content', False):
                break
    return body


async def get_stream(body: http.Body):
    return io.BytesIO(body)


def _get_content_length(headers: http.Headers) -> typing.Optional[int]:
    content_length = headers.get('Content-Length')
    if content_length is not None:
        try:
            return max(0, int(content_length))
        except (ValueError, TypeError):  # pragma: nocover
            pass
    return None  # pragma: nocover


async def get_request_data(headers: http.Headers, injector: Injector, settings: Settings):
    content_type = headers.get('Content-Type')
    if not content_type:
        return None

    media_type, _ = parse_options_header(content_type)
    parser_mapping = {
        parser.media_type: parser
        for parser in settings.get('PARSERS', parsers.DEFAULT_PARSERS)
    }

    if media_type not in parser_mapping:
        raise exceptions.UnsupportedMediaType()

    parser = parser_mapping[media_type]
    return await injector.run_async(parser.parse)


async def get_auth(handler: Handler, injector: Injector, settings: Settings):
    default_authentication = settings.get('AUTHENTICATION', None)
    authentication = getattr(handler, 'authentication', default_authentication)
    if authentication is None:
        return Unauthenticated()

    for authenticator in authentication:
        auth = await injector.run_async(authenticator.authenticate)
        if auth is not None:
            return auth
    return Unauthenticated()


def get_file_wrapper():
    # The Uvicorn Messaging Interface doesn't yet support any equivelent
    # to wsgi.file_wrapper.
    def _wrapper(file):
        return file.read()
    return _wrapper
