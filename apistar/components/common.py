from apistar import http
from apistar.interfaces import URLArgs, ParamName


def lookup_header(name: ParamName, headers: http.Headers):
    return headers.get(name.replace('_', '-'))


def lookup_queryparam(name: ParamName, queryparams: http.QueryParams):
    return queryparams.get(name)


def lookup_url_arg(name: ParamName, args: URLArgs):
    return args.get(name)
