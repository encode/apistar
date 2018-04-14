import mimetypes

import requests

from apistar import codecs, conneg, exceptions
from apistar.client.utils import (
    BlockAllCookies, File, ForceMultiPartDict, guess_filename, is_file
)


class BaseTransport():
    schemes = None

    def send(self, method, url, query_params=None, content=None, encoding=None):
        raise NotImplementedError()


class HTTPTransport(BaseTransport):
    schemes = ['http', 'https']
    default_decoders = [
        codecs.JSONCodec(),
        codecs.TextCodec(),
        codecs.DownloadCodec()
    ]

    def __init__(self, auth=None, decoders=None, headers=None, session=None):
        from apistar import __version__

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
            'user-agent': 'apistar %s' % __version__
        }
        if headers:
            self.headers.update({
                key.lower(): value
                for key, value in headers.items()
            })

    def send(self, method, url, query_params=None, content=None, encoding=None):
        options = self.get_request_options(query_params, content, encoding)
        response = self.session.request(method, url, **options)
        result = self.decode_response_content(response)

        if 400 <= response.status_code <= 599:
            title = '%d %s' % (response.status_code, response.reason)
            raise exceptions.ErrorResponse(title, result)

        return result

    def get_request_options(self, query_params, content, encoding):
        """
        Returns a dictionary of keyword parameters to include when making
        the outgoing request.
        """
        options = {
            'headers': dict(self.headers)
        }

        if query_params:
            options['params'] = query_params

        if content is not None:
            if encoding == 'application/json':
                options['json'] = content
            elif encoding == 'multipart/form-data':
                data = {}
                files = ForceMultiPartDict()
                for key, value in content.items():
                    if is_file(value):
                        files[key] = value
                    else:
                        data[key] = value
            elif encoding == 'application/x-www-form-urlencoded':
                options['data'] = content
            elif encoding == 'application/octet-stream':
                if isinstance(content, File):
                    options['data'] = content.content
                else:
                    options['data'] = content
                upload_headers = self.get_upload_headers(content)
                options['headers'].update(upload_headers)

        return options

    def get_upload_headers(self, file_obj):
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

    def decode_response_content(self, response):
        """
        Given an HTTP response, return the decoded data.
        """
        if not response.content:
            return None

        content_type = response.headers.get('content-type')
        codec = conneg.negotiate_content_type(self.decoders, content_type)

        options = {
            'base_url': response.url
        }
        if 'content-type' in response.headers:
            options['content_type'] = response.headers['content-type']
        if 'content-disposition' in response.headers:
            options['content_disposition'] = response.headers['content-disposition']

        return codec.decode(response.content, **options)
