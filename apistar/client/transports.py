import collections
import mimetypes

import requests
import uritemplate

from coreapi import exceptions, utils
from coreapi.compat import cookiejar
from coreapi.transports.base import BaseTransport
from coreapi.utils import File, guess_filename, is_file

Params = collections.namedtuple('Params', ['path', 'query', 'data', 'files'])
empty_params = Params({}, {}, {}, {})


class ForceMultiPartDict(dict):
    """
    A dictionary that always evaluates as True.
    Allows us to force requests to use multipart encoding, even when no
    file parameters are passed.
    """
    def __bool__(self):
        return True

    def __nonzero__(self):
        return True


class BlockAll(cookiejar.CookiePolicy):
    """
    A cookie policy that rejects all cookies.
    Used to override the default `requests` behavior.
    """
    return_ok = set_ok = domain_return_ok = path_return_ok = lambda self, *args, **kwargs: False
    netscape = True
    rfc2965 = hide_cookie2 = False


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

    # Ensure graceful behavior in edge-case where both location='body' and
    # location='form' fields are present.
    seen_body = False

    for key, value in params.items():
        if key not in field_map or not field_map[key].location:
            # Default is 'query' for 'GET' and 'DELETE', and 'form' for others.
            location = 'query' if method in ('GET', 'DELETE') else 'form'
        else:
            location = field_map[key].location

        if location == 'form' and encoding == 'application/octet-stream':
            # Raw uploads should always use 'body', not 'form'.
            location = 'body'

        try:
            if location == 'path':
                path[key] = utils.validate_path_param(value)
            elif location == 'query':
                query[key] = utils.validate_query_param(value)
            elif location == 'body':
                data = utils.validate_body_param(value, encoding=encoding)
                seen_body = True
            elif location == 'form':
                if not seen_body:
                    data[key] = utils.validate_form_param(value, encoding=encoding)
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
        return uritemplate.expand(url, path_params)
    return url


def _get_headers(url, decoders):
    """
    Return a dictionary of HTTP headers to use in the outgoing request.
    """
    accept_media_types = decoders[0].get_media_types()
    if '*/*' not in accept_media_types:
        accept_media_types.append('*/*')

    headers = {
        'accept': ', '.join(accept_media_types),
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
    codec = utils.negotiate_decoder(decoders, content_type)

    options = {
        'base_url': response.url
    }
    if 'content-type' in response.headers:
        options['content_type'] = response.headers['content-type']
    if 'content-disposition' in response.headers:
        options['content_disposition'] = response.headers['content-disposition']

    return codec.decode(response.content, **options)


class HTTPTransport(BaseTransport):
    schemes = ['http', 'https']

    def __init__(self, auth=None, headers=None, session=None):
        if session is None:
            session = requests.Session()
        if auth is not None:
            session.auth = auth
        if headers:
            headers = {key.lower(): value for key, value in headers.items()}

        if not getattr(session.auth, 'allow_cookies', False):
            session.cookies.set_policy(BlockAll())

        self.headers = {} if (headers is None) else dict(headers)
        self.session = session

    def transition(self, link, decoders, params=None):
        method = _get_method(link.method)
        encoding = _get_encoding(link.encoding)
        params = _get_params(method, encoding, link.fields, params)
        url = _get_url(link.url, params.path)
        headers = _get_headers(url, decoders)
        headers.update(self.headers)

        options = _get_request_options(headers, encoding, params)
        response = self.session.request(method, url, **options)
        content = _decode_result(response, decoders)

        if response.status_code >= 400 and response.status_code <= 599:
            title = '%d %s' % (response.status_code, response.reason)
            raise exceptions.ErrorMessage(title, content)

        return content
