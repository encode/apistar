from typing import Union


class Marker():
    def __init__(self, position, content=None):
        self.position = position
        self.content = content
        if content is None:
            self.line_number = None
            self.column_number = None
        else:
            lines = content[:position + 1].splitlines()
            self.line_number = len(lines)
            self.column_number = len(lines[-1]) if lines else 1

    def __eq__(self, other):
        return self.position == other.position


class ErrorMessage():
    def __init__(self, message, marker):
        self.message = message
        self.marker = marker

    def __repr__(self):
        return '%s(%s, position=%d)' % (
            self.__class__.__name__,
            repr(self.message),
            self.marker.position
        )

    def __eq__(self, other):
        return self.message == other.message and self.marker == other.marker


class ValidationError(Exception):
    def __init__(self, detail):
        assert isinstance(detail, (str, dict))
        self.detail = detail
        super(ValidationError, self).__init__(detail)

    def set_error_context(self, token, content):
        self.token = token
        self.content = content

    def get_error_messages(self):
        assert self.token is not None, 'set_error_context() not called.'
        error_messages = []
        for prefix, message in self._walk_error_details(self.detail):
            lookup_property = message.code in ('invalid_key', 'invalid_property')
            if message.code == 'required':
                prefix = prefix[:-1]
            position = self.token.lookup(prefix, lookup_property=lookup_property).start
            marker = Marker(position, self.content)
            error_message = ErrorMessage(message, marker)
            error_messages.append(error_message)
        return sorted(error_messages, key=lambda e: e.marker.position)

    def _walk_error_details(self, error_detail, prefix=()):
        """
        Given an 'error_detail' from a ValidationError, returns a list of
        two-tuples of (index, message).
        """
        pairs = []
        if isinstance(error_detail, str):
            pairs.append((prefix, error_detail))
        elif isinstance(error_detail, dict):
            for key, value in error_detail.items():
                pairs.extend(self._walk_error_details(value, prefix + (key,)))
        return pairs


class ParseError(Exception):
    """
    Raised by a Codec when `decode` fails due to malformed syntax.
    """
    def __init__(self, message, marker=None, base_format=None):
        Exception.__init__(self, message)
        self.message = message
        self.marker = marker
        self.base_format = base_format

    def get_error_messages(self):
        assert self.marker is not None, 'No marker set.'
        return [ErrorMessage(self.message, self.marker)]


class NoReverseMatch(Exception):
    """
    Raised by a Router when `reverse_url` is passed an invalid handler name.
    """
    pass


class ErrorResponse(Exception):
    """
    Raised when a client request results in an error response being returned.
    """
    def __init__(self, title, content):
        self.title = title
        self.content = content


class RequestError(Exception):
    """
    Raised when some invalid parameter is used in a client request.
    """
    pass


class NoCodecAvailable(Exception):
    pass


class ConfigurationError(Exception):
    pass


# HTTP exceptions

class HTTPException(Exception):
    default_status_code = None  # type: int
    default_detail = None  # type: str

    def __init__(self,
                 detail: Union[str, dict]=None,
                 status_code: int=None) -> None:
        self.detail = self.default_detail if (detail is None) else detail
        self.status_code = self.default_status_code if (status_code is None) else status_code
        assert self.detail is not None, '"detail" is required.'
        assert self.status_code is not None, '"status_code" is required.'

    def get_headers(self):
        return {}


class Found(HTTPException):
    default_status_code = 302
    default_detail = 'Found'

    def __init__(self,
                 location: str,
                 detail: Union[str, dict]=None,
                 status_code: int=None) -> None:
        self.location = location
        super().__init__(detail, status_code)

    def get_headers(self):
        return {'Location': self.location}


class BadRequest(HTTPException):
    default_status_code = 400
    default_detail = 'Bad request'


class Forbidden(HTTPException):
    default_status_code = 403
    default_detail = 'Forbidden'


class NotFound(HTTPException):
    default_status_code = 404
    default_detail = 'Not found'


class MethodNotAllowed(HTTPException):
    default_status_code = 405
    default_detail = 'Method not allowed'


class NotAcceptable(HTTPException):
    default_status_code = 406
    default_detail = 'Could not satisfy the request Accept header'


class UnsupportedMediaType(HTTPException):
    default_status_code = 415
    default_detail = 'Unsupported Content-Type header in request'
