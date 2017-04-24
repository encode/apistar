class ConfigurationError(Exception):
    pass


class SchemaError(Exception):
    def __init__(self, detail):
        self.detail = detail
        super().__init__(detail)


# Handled exceptions

class APIException(Exception):
    default_status_code = 500
    default_message = 'Server error'

    def __init__(self, message=None, status_code=None):
        self.message = self.default_message if (message is None) else message
        self.status_code = self.default_status_code if (status_code is None) else status_code


class ValidationError(APIException):
    default_status_code = 400
    default_message = 'Invalid request'


class NotFound(APIException):
    default_status_code = 404
    default_message = 'Not found'


class MethodNotAllowed(APIException):
    default_status_code = 405
    default_message = 'Method not allowed'
