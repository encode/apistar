from typing import Union


class TypeSystemError(Exception):
    def __init__(self,
                 detail: Union[str, dict]=None) -> None:
        self.detail = detail
        super().__init__(detail)


class NoReverseMatch(Exception):
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


class NotFound(HTTPException):
    default_status_code = 404
    default_detail = 'Not found'


class MethodNotAllowed(HTTPException):
    default_status_code = 405
    default_detail = 'Method not allowed'


class UnsupportedMediaType(HTTPException):
    default_status_code = 415
    default_detail = 'Unsupported media type'
