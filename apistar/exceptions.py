from typing import Union
from apistar.schema import String, Number, Integer, Boolean

class SchemaError(Exception):

    def __init__(self, schema: Union[String, Number, Integer, Boolean], code: str) -> None:
        self.schema = schema
        self.code = code
        msg = schema.errors[code].format(**schema.__dict__)
        super().__init__(msg)


class ConfigurationError(Exception):
    pass


# Handled exceptions

class APIException(Exception):
    default_status_code = 500
    default_message = 'Server error'

    def __init__(self, status_code:int = None, message:str = None) -> None:
        self.status_code = self.default_status_code if (status_code is None) else status_code
        self.message = self.default_message if (message is None) else message


class ValidationError(APIException):
    default_status_code = 400
    default_message = 'Invalid request'


class NotFound(APIException):
    default_status_code = 404
    default_message = 'Not found'


class MethodNotAllowed(APIException):
    default_status_code = 405
    default_message = 'Method not allowed'
