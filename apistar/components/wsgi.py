from apistar.interfaces import WSGIEnviron
import werkzeug


def get_headers(environ: WSGIEnviron):
    return werkzeug.datastructures.EnvironHeaders(environ)


def get_queryparams(environ: WSGIEnviron):
    return werkzeug.urls.url_decode(environ.get('QUERY_STRING', ''))


def get_body(environ: WSGIEnviron):
    return environ['input.stream'].read()
