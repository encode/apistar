from apistar.interfaces import URLArgs, Headers, QueryParams, ParamName


def lookup_header(name: ParamName, headers: Headers):
    return headers.get(name.replace('_', '-'))


def lookup_queryparam(name: ParamName, queryparams: QueryParams):
    return queryparams.get(name)


def lookup_url_arg(name: ParamName, args: URLArgs):
    return args.get(name)
