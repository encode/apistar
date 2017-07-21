from typing import Union


class ConfigurationError(Exception):
    pass


class InternalError(Exception):
    pass


class SchemaError(Exception):
    def __init__(self, detail: Union[str, dict]) -> None:
        self.detail = detail
        super().__init__(detail)


# Handled exceptions

class APIException(Exception):
    default_status_code = 500
    default_detail = 'Server error'

    def __init__(self,
                 detail: Union[str, dict]=None,
                 status_code: int=None) -> None:
        self.detail = self.default_detail if (detail is None) else detail
        self.status_code = self.default_status_code if (status_code is None) else status_code


class Found(APIException):
    default_status_code = 302
    default_detail = ''

    def __init__(self,
                 location: str,
                 detail: Union[str, dict]=None,
                 status_code: int=None) -> None:
        self.location = location
        super().__init__(detail, status_code)


class ValidationError(APIException):
    default_status_code = 400
    default_detail = 'Invalid request'


class NotFound(APIException):
    default_status_code = 404
    default_detail = 'Not found'


class MethodNotAllowed(APIException):
    default_status_code = 405
    default_detail = 'Method not allowed'


class UnsupportedMediaType(APIException):
    default_status_code = 415
    default_detail = 'Unsupported media type in request'


class NoReverseMatch(APIException):
    """Exception for when no route was found when reversing a view to a URL.
    Triggered by routing.Router.reverse_url() on a method not mapped to a view or route.
    """
    default_status_code = 500
    default_detail = 'No reverse match found for view'
