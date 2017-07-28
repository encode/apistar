import typing


class SchemaError(Exception):
    def __init__(self, detail: typing.Union[str, dict]) -> None:
        self.detail = detail
        super().__init__(detail)


class ValidationError(Exception):
    def __init__(self, detail: typing.Union[str, dict]) -> None:
        self.detail = detail
        super().__init__(detail)
