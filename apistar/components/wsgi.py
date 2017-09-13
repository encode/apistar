from wsgiref.util import FileWrapper, request_uri

import werkzeug
from werkzeug.http import parse_options_header
from werkzeug.wsgi import get_input_stream

from apistar import Settings, exceptions, http, parsers
from apistar.authentication import Unauthenticated
from apistar.interfaces import Injector
from apistar.types import Handler, ParamName, WSGIEnviron


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


def get_stream(environ: WSGIEnviron):
    return get_input_stream(environ)


def get_request_data(headers: http.Headers, injector: Injector, settings: Settings):
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
    return injector.run(parser.parse)


def get_auth(handler: Handler, injector: Injector, settings: Settings):
    default_authentication = settings.get('AUTHENTICATION', None)
    authentication = getattr(handler, 'authentication', default_authentication)
    if authentication is None:
        return Unauthenticated()

    for authenticator in authentication:
        auth = injector.run(authenticator.authenticate)
        if auth is not None:
            return auth
    return Unauthenticated()


def get_file_wrapper(environ: WSGIEnviron):
    return environ.get('wsgi.file_wrapper', FileWrapper)
