import json
from wsgiref.util import FileWrapper, request_uri

import werkzeug
from werkzeug.datastructures import ImmutableMultiDict
from werkzeug.formparser import FormDataParser
from werkzeug.http import parse_options_header
from werkzeug.wsgi import get_input_stream

from apistar import exceptions, http
from apistar.types import ParamName, WSGIEnviron


def get_method(environ: WSGIEnviron):
    return environ['REQUEST_METHOD'].upper()


def get_url(environ: WSGIEnviron):
    return http.URL(request_uri(environ))


def get_scheme(environ: WSGIEnviron):
    return environ['wsgi.url_scheme']


def get_host(environ: WSGIEnviron):
    return environ.get('HTTP_HOST') or environ['SERVER_NAME']


def get_port(environ: WSGIEnviron):
    if environ['wsgi.url_scheme'] == 'https':
        return int(environ.get('SERVER_PORT') or 443)
    return int(environ.get('SERVER_PORT') or 80)


def get_path(environ: WSGIEnviron):
    return environ['SCRIPT_NAME'] + environ['PATH_INFO']


def get_querystring(environ: WSGIEnviron):
    return environ.get('QUERY_STRING', '')


def get_queryparams(environ: WSGIEnviron) -> http.QueryParams:
    return werkzeug.urls.url_decode(
        environ.get('QUERY_STRING', ''),
        cls=http.QueryParams
    )


def get_queryparam(name: ParamName, queryparams: http.QueryParams):
    return queryparams.get(name)


def get_headers(environ: WSGIEnviron) -> http.Headers:
    header_items = []
    for key, value in environ.items():
        if key.startswith('HTTP_'):
            header = (key[5:].lower().replace('_', '-'), value)
            header_items.append(header)
        elif key in ('CONTENT_TYPE', 'CONTENT_LENGTH'):
            header = (key.lower().replace('_', '-'), value)
            header_items.append(header)
    return http.Headers(header_items)


def get_header(name: ParamName, headers: http.Headers):
    return headers.get(name.replace('_', '-'))


def get_body(environ: WSGIEnviron):
    return get_input_stream(environ).read()


def get_request_data(environ: WSGIEnviron):
    if not bool(environ.get('CONTENT_TYPE')):
        mimetype = None
    else:
        mimetype, _ = parse_options_header(environ['CONTENT_TYPE'])

    if mimetype is None:
        value = None
    elif mimetype == 'application/json':
        body = get_body(environ)
        if not body:
            raise exceptions.EmptyJSON()
        try:
            value = json.loads(body.decode('utf-8'))
        except json.JSONDecodeError:
            raise exceptions.InvalidJSON()
    elif mimetype in ('multipart/form-data', 'application/x-www-form-urlencoded'):
        parser = FormDataParser()
        stream, form, files = parser.parse_from_environ(environ)
        value = ImmutableMultiDict(list(form.items()) + list(files.items()))
    else:
        raise exceptions.UnsupportedMediaType()

    return value


def get_file_wrapper(environ: WSGIEnviron):
    return environ.get('wsgi.file_wrapper', FileWrapper)
