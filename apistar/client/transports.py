import collections
import mimetypes

import requests

from apistar import codecs, conneg, exceptions
from apistar.client.utils import (
    BlockAllCookies, File, ForceMultiPartDict, guess_filename, is_file
)

Params = collections.namedtuple('Params', ['path', 'query', 'data', 'files'])
empty_params = Params({}, {}, {}, {})


def _get_method(method):
    if not method:
        return 'GET'
    return method.upper()


def _get_encoding(encoding):
    if not encoding:
        return 'application/json'
    return encoding


def _get_params(method, encoding, fields, params=None):
    """
    Separate the params into the various types.
    """
    if params is None:
        return empty_params

    field_map = {field.name: field for field in fields}

    path = {}
    query = {}
    data = {}
    files = {}

    errors = {}

    for key, value in params.items():
        if key not in field_map:
            continue

        location = field_map[key].location

        try:
            if location == 'path':
                path[key] = value
            elif location == 'query':
                query[key] = value
            elif location == 'body':
                data = value
        except exceptions.ParameterError as exc:
            errors[key] = "%s" % exc

    if errors:
        raise exceptions.ParameterError(errors)

    # Move any files from 'data' into 'files'.
    if isinstance(data, dict):
        for key, value in list(data.items()):
            if is_file(data[key]):
                files[key] = data.pop(key)

    return Params(path, query, data, files)


def _get_url(url, path_params):
    """
    Given a templated URL and some parameters that have been provided,
    expand the URL.
    """
    if path_params:
        for key, value in path_params:
            url = url.replace('{%s}' % key, value)
    return url


def _get_headers(decoders):
    """
    Return a dictionary of HTTP headers to use in the outgoing request.
    """
    headers = {
        'accept': '%s, */*' % decoders[0].media_type,
        'user-agent': 'coreapi'
    }

    return headers


def _get_upload_headers(file_obj):
    """
    When a raw file upload is made, determine the Content-Type and
    Content-Disposition headers to use with the request.
    """
    name = guess_filename(file_obj)
    content_type = None
    content_disposition = None

    # Determine the content type of the upload.
    if getattr(file_obj, 'content_type', None):
        content_type = file_obj.content_type
    elif name:
        content_type, encoding = mimetypes.guess_type(name)

    # Determine the content disposition of the upload.
    if name:
        content_disposition = 'attachment; filename="%s"' % name

    return {
        'Content-Type': content_type or 'application/octet-stream',
        'Content-Disposition': content_disposition or 'attachment'
    }


def _get_request_options(headers, encoding, params):
    """
    Returns a dictionary of keyword parameters to include when making
    the outgoing request.
    """
    options = {
        "headers": headers or {}
    }

    if params.query:
        options['params'] = params.query

    if params.data or params.files:
        if encoding == 'application/json':
            options['json'] = params.data
        elif encoding == 'multipart/form-data':
            options['data'] = params.data
            options['files'] = ForceMultiPartDict(params.files)
        elif encoding == 'application/x-www-form-urlencoded':
            options['data'] = params.data
        elif encoding == 'application/octet-stream':
            if isinstance(params.data, File):
                options['data'] = params.data.content
            else:
                options['data'] = params.data
            upload_headers = _get_upload_headers(params.data)
            headers.update(upload_headers)

    return options


def _decode_result(response, decoders):
    """
    Given an HTTP response, return the decoded data.
    """
    if not response.content:
        return None

    content_type = response.headers.get('content-type')
    codec = conneg.negotiate_content_type(decoders, content_type)

    options = {
        'base_url': response.url
    }
    if 'content-type' in response.headers:
        options['content_type'] = response.headers['content-type']
    if 'content-disposition' in response.headers:
        options['content_disposition'] = response.headers['content-disposition']

    return codec.decode(response.content, **options)


class BaseTransport():
    schemes = None

    def transition(self, url, link, decoders, params=None):
        raise NotImplementedError()


class HTTPTransport(BaseTransport):
    schemes = ['http', 'https']
    default_decoders = [
        codecs.JSONCodec(),
        codecs.TextCodec(),
        codecs.DownloadCodec()
    ]

    def __init__(self, decoders=None, auth=None, headers=None, session=None):
        if session is None:
            session = requests.Session()
        if auth is not None:
            session.auth = auth
        if not getattr(session.auth, 'allow_cookies', False):
            session.cookies.set_policy(BlockAllCookies())

        self.session = session
        self.decoders = list(decoders) if decoders else list(self.default_decoders)
        self.headers = {
            'accept': '%s, */*' % self.decoders[0].media_type,
            'user-agent': 'coreapi'
        }
        if headers:
            self.headers.update({
                key.lower(): value
                for key, value in headers.items()
            })

    def transition(self, url, link, params=None):
        method = _get_method(link.method)
        encoding = _get_encoding(link.encoding)
        params = _get_params(method, encoding, link.fields, params)
        url = _get_url(url, params.path)
        headers = _get_headers(self.decoders)
        headers.update(self.headers)

        options = _get_request_options(headers, encoding, params)
        response = self.session.request(method, url, **options)
        content = _decode_result(response, self.decoders)

        if response.status_code >= 400 and response.status_code <= 599:
            title = '%d %s' % (response.status_code, response.reason)
            raise exceptions.ErrorResponse(title, content)

        return content
