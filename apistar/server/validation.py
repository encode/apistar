import inspect
import typing

from apistar import exceptions, types
from apistar.document import Link
from apistar.server import http
from apistar.server.injector import Component

ValidatedPathParams = typing.NewType('ValidatedPathParams', dict)
ValidatedQueryParams = typing.NewType('ValidatedQueryParams', dict)


class ValidatePathParamsComponent(Component):
    resolves = (ValidatedPathParams,)

    def resolve_parameter(self,
                          link: Link,
                          path_params: http.PathParams):
        path_fields = link.get_path_fields()

        validator = types.Object(
            properties=[
                (field.name, field.schema if field.schema else types.Any())
                for field in path_fields
            ],
            required=[field.name for field in path_fields]
        )

        try:
            path_params = validator.validate(path_params, allow_coerce=True)
        except types.ValidationError as exc:
            raise exceptions.NotFound(exc.detail)
        return path_params


class ValidatedParamComponent(Component):
    resolves = (str, int, float, bool)

    def handle_parameter(self, parameter: inspect.Parameter):
        if parameter.annotation is parameter.empty:
            return True
        return parameter.annotation in self.resolves

    def resolve_parameter(self,
                          parameter: inspect.Parameter,
                          path_params: ValidatedPathParams):
        param_validator = {
            parameter.empty: types.Any(),
            str: types.String(),
            int: types.Integer(),
            float: types.Number(),
            bool: types.Boolean()
        }[parameter.annotation]

        validator = types.Object(
            properties=[(parameter.name, param_validator)],
            required=[parameter.name]
        )

        try:
            path_params = validator.validate(path_params, allow_coerce=True)
        except types.ValidationError as exc:
            raise exceptions.NotFound(exc.detail)
        return path_params[parameter.name]


VALIDATION_COMPONENTS = (
    ValidatePathParamsComponent(),
    ValidatedParamComponent()
)
