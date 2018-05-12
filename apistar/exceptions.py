from typing import Union


class ValidationError(Exception):
    def __init__(self, detail, value=None):
        assert isinstance(detail, (str, dict))
        self.detail = detail
        self.value = value
        super(ValidationError, self).__init__(detail)


class ParseError(Exception):
    """
    Raised by a Codec when `decode` fails due to malformed syntax.
    """
    def __init__(self, message, short_message=None, pos=None, lineno=None, colno=None):
        Exception.__init__(self, message)
        self.message = message
        self.short_message = short_message
        self.pos = pos
        self.lineno = lineno
        self.colno = colno


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
