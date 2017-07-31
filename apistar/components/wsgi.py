from apistar import exceptions
from apistar.interfaces import WSGIEnviron
from urllib.parse import quote
from werkzeug.datastructures import ImmutableMultiDict
from werkzeug.formparser import parse_form_data
from werkzeug.http import parse_options_header
from werkzeug.wsgi import get_input_stream
import json
import werkzeug


def get_url(environ: WSGIEnviron):
    # https://www.python.org/dev/peps/pep-0333/#url-reconstruction
    url = environ['wsgi.url_scheme'] + '://'

    if environ.get('HTTP_HOST'):
        url += environ['HTTP_HOST']
    else:
        url += environ['SERVER_NAME']

        if environ['wsgi.url_scheme'] == 'https':
            if environ['SERVER_PORT'] != '443':
                url += ':' + environ['SERVER_PORT']
        else:
            if environ['SERVER_PORT'] != '80':
                url += ':' + environ['SERVER_PORT']

    url += quote(environ.get('SCRIPT_NAME', ''))
    url += quote(environ.get('PATH_INFO', ''))
    if environ.get('QUERY_STRING'):
        url += '?' + environ['QUERY_STRING']

    return url


def get_scheme(environ: WSGIEnviron):
    return environ['wsgi.url_scheme']


def get_host(environ: WSGIEnviron):
    return environ.get('HTTP_HOST') or environ['SERVER_NAME']


def get_port(environ: WSGIEnviron):
    if environ['wsgi.url_scheme'] == 'https':
        return int(environ.get('SERVER_PORT') or 443)
    return int(environ.get('SERVER_PORT') or 80)


def get_path(environ: WSGIEnviron):
    return quote(environ.get('SCRIPT_NAME', '') + environ.get('PATH_INFO', ''))


def get_querystring(environ: WSGIEnviron):
    return environ.get('QUERY_STRING', '')


def get_queryparams(environ: WSGIEnviron):
    return werkzeug.urls.url_decode(environ.get('QUERY_STRING', ''))


def get_headers(environ: WSGIEnviron):
    return werkzeug.datastructures.EnvironHeaders(environ)


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
        body = get_input_stream(environ).read()
        value = json.loads(body.decode('utf-8'))
    elif mimetype in ('multipart/form-data', 'application/x-www-form-urlencoded'):
        stream, form, files = parse_form_data(environ)
        value = ImmutableMultiDict(list(form.items()) + list(files.items()))
    else:
        raise exceptions.UnsupportedMediaType()

    return value
