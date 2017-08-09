import werkzeug

from apistar import http
from apistar.interfaces import ParamName, UMIMessage


def get_method(message: UMIMessage):
    return message['method'].upper()


# def get_url(message: UMIMessage):
#     return request_uri(environ)


def get_scheme(message: UMIMessage):
    return message['scheme']


def get_host(message: UMIMessage):
    return message['server'][0]


def get_port(message: UMIMessage):
    return message['server'][1]


def get_path(message: UMIMessage):
    return message['path']


def get_querystring(message: UMIMessage):
    return message['query_string']


def get_queryparams(message: UMIMessage):
    return werkzeug.urls.url_decode(message['query_string'])


def get_queryparam(name: ParamName, queryparams: http.QueryParams):
    return queryparams.get(name)


# def get_headers(environ: WSGIEnviron):
#     return werkzeug.datastructures.EnvironHeaders(environ)


# def get_header(name: ParamName, headers: http.Headers):
#     return headers.get(name.replace('_', '-'))


# def get_body(environ: WSGIEnviron):
#     return get_input_stream(environ).read()


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
