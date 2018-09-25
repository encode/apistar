import http

import requests

from apistar import exceptions
from apistar.client import decoders, encoders


class BlockAllCookies(http.cookiejar.CookiePolicy):
    """
    A cookie policy that rejects all cookies.
    Used to override the default `requests` behavior.
    """
    return_ok = set_ok = domain_return_ok = path_return_ok = lambda self, *args, **kwargs: False
    netscape = True
    rfc2965 = hide_cookie2 = False


class BaseTransport():
    schemes = None

    def send(self, method, url, query_params=None, content=None, encoding=None):
        raise NotImplementedError()


class HTTPTransport(BaseTransport):
    schemes = ['http', 'https']
    default_decoders = [
        decoders.JSONDecoder(),
        decoders.TextDecoder(),
        decoders.DownloadDecoder()
    ]
    default_encoders = [
        encoders.JSONEncoder(),
        encoders.MultiPartEncoder(),
        encoders.URLEncodedEncoder(),
    ]

    def __init__(self, auth=None, decoders=None, encoders=None, headers=None, session=None, allow_cookies=True):
        from apistar import __version__

        if session is None:
            session = requests.Session()
        if auth is not None:
            session.auth = auth
        if not allow_cookies:
            session.cookies.set_policy(BlockAllCookies())

        self.session = session
        self.decoders = list(decoders) if decoders else list(self.default_decoders)
        self.encoders = list(encoders) if encoders else list(self.default_encoders)
        self.headers = {
            'accept': ', '.join([decoder.media_type for decoder in self.decoders]),
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
            raise exceptions.ErrorResponse(
                title=title,
                status_code=response.status_code,
                content=result
            )

        return result

    def get_encoder(self, encoding):
        """
        Given the value of the encoding, return the appropriate encoder for
        handling the request content.
        """
        content_type = encoding.split(';')[0].strip().lower()
        main_type = content_type.split('/')[0] + '/*'
        wildcard_type = '*/*'

        for codec in self.encoders:
            if codec.media_type in (content_type, main_type, wildcard_type):
                return codec

        text = "Unsupported encoding '%s' for request." % encoding
        message = exceptions.ErrorMessage(text=text, code='cannot-encode-request')
        raise exceptions.ClientError(messages=[message])

    def get_decoder(self, content_type=None):
        """
        Given the value of a 'Content-Type' header, return the appropriate
        decoder for handling the response content.
        """
        if content_type is None:
            return self.decoders[0]

        content_type = content_type.split(';')[0].strip().lower()
        main_type = content_type.split('/')[0] + '/*'
        wildcard_type = '*/*'

        for codec in self.decoders:
            if codec.media_type in (content_type, main_type, wildcard_type):
                return codec

        text = "Unsupported encoding '%s' in response Content-Type header." % content_type
        message = exceptions.ErrorMessage(text=text, code='cannot-decode-response')
        raise exceptions.ClientError(messages=[message])

    def get_request_options(self, query_params=None, content=None, encoding=None):
        """
        Return the 'options' for sending the outgoing request.
        """
        options = {
            'headers': dict(self.headers),
            'params': query_params
        }

        if content is None:
            return options

        encoder = self.get_encoder(encoding)
        encoder.encode(options, content)
        return options

    def decode_response_content(self, response):
        """
        Given an HTTP response, return the decoded data.
        """
        if not response.content:
            return None

        content_type = response.headers.get('content-type')
        decoder = self.get_decoder(content_type)
        return decoder.decode(response)
