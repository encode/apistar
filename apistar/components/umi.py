import werkzeug

from apistar import http
from apistar.interfaces import ParamName, UMIChannels, UMIMessage


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

    return url


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
    if 'body' in channels:
        while True:
            message_chunk = await channels['body'].receive()
            body += message_chunk['content']
            if not message_chunk.get('more_content', False):
                break
    return body


# def get_request_data(environ: WSGIEnviron):
#     if not bool(environ.get('CONTENT_TYPE')):
#         mimetype = None
#     else:
#         mimetype, _ = parse_options_header(environ['CONTENT_TYPE'])
#
#     if mimetype is None:
#         value = None
#     elif mimetype == 'application/json':
#         body = get_input_stream(environ).read()
#         value = json.loads(body.decode('utf-8'))
#     elif mimetype in ('multipart/form-data', 'application/x-www-form-urlencoded'):
#         stream, form, files = parse_form_data(environ)
#         value = ImmutableMultiDict(list(form.items()) + list(files.items()))
#     else:
#         raise exceptions.UnsupportedMediaType()
#
#     return value
