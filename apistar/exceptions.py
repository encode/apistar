from typing import Union


class TypeSystemError(Exception):
    def __init__(self,
                 detail: Union[str, dict]=None,
                 cls: type=None,
                 code: str=None) -> None:

        if cls is not None and code is not None:
            errors = getattr(cls, 'errors')
            detail = errors[code].format(**cls.__dict__)

        self.detail = detail
        super().__init__(detail)


class NoReverseMatch(Exception):
    pass


class TemplateNotFound(Exception):
    pass


class CouldNotResolveDependency(Exception):
    pass


class ConfigurationError(Exception):
    pass


class CommandLineError(Exception):
    def __init__(self, message: str, exit_code: int=1) -> None:
        self.exit_code = exit_code
        self.message = message
        super().__init__(message)


class CommandLineExit(Exception):
    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)


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


class Found(HTTPException):
    default_status_code = 302
    default_detail = 'Found'

    def __init__(self,
                 location: str,
                 detail: Union[str, dict]=None,
                 status_code: int=None) -> None:
        self.location = location
        super().__init__(detail, status_code)


class ValidationError(HTTPException):
    default_status_code = 400
    default_detail = 'Validation error'


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
    default_detail = 'Unsupported media type'
