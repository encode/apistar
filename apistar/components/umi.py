import io
import json
import typing

import werkzeug
from werkzeug.datastructures import ImmutableMultiDict
from werkzeug.formparser import FormDataParser
from werkzeug.http import parse_options_header

from apistar import exceptions, http
from apistar.types import ParamName, UMIChannels, UMIMessage


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


def _get_content_length(headers: http.Headers) -> typing.Optional[int]:
    content_length = headers.get('Content-Length')
    if content_length is not None:
        try:
            return max(0, int(content_length))
        except (ValueError, TypeError):  # pragma: nocover
            pass
    return None  # pragma: nocover


async def get_request_data(headers: http.Headers, message: UMIMessage, channels: UMIChannels):
    content_type = headers.get('Content-Type')
    if content_type:
        mimetype, options = parse_options_header(content_type)
    else:
        mimetype, options = None, {}

    if mimetype is None:
        value = None
    elif mimetype == 'application/json':
        body = await get_body(message, channels)
        if not body:
            raise exceptions.EmptyJSON()
        try:
            value = json.loads(body.decode('utf-8'))
        except json.JSONDecodeError:
            raise exceptions.InvalidJSON()
    elif mimetype in ('multipart/form-data', 'application/x-www-form-urlencoded'):
        body = await get_body(message, channels)
        stream = io.BytesIO(body)
        content_length = _get_content_length(headers)
        parser = FormDataParser()
        stream, form, files = parser.parse(stream, mimetype, content_length, options)
        value = ImmutableMultiDict(list(form.items()) + list(files.items()))
    else:
        raise exceptions.UnsupportedMediaType()

    return value


def get_file_wrapper():
    # The Uvicorn Messaging Interface doesn't yet support any equivelent
    # to wsgi.file_wrapper.
    def _wrapper(file):
        return file.read()
    return _wrapper
