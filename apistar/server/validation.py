import inspect
import typing

from apistar import codecs, exceptions, http, types
from apistar.conneg import negotiate_content_type
from apistar.document import Link
from apistar.server.components import Component

ValidatedPathParams = typing.NewType('ValidatedPathParams', dict)
ValidatedQueryParams = typing.NewType('ValidatedQueryParams', dict)


class RequestDataComponent(Component):
    resolves_types = (http.RequestData,)

    def __init__(self):
        self.codecs = [codecs.JSONCodec()]

    def resolve(self,
                content: http.Body,
                headers: http.Headers):
        if not content:
            return None

        content_type = headers.get('Content-Type')

        try:
            codec = negotiate_content_type(self.codecs, content_type)
        except exceptions.NoCodecAvailable:
            raise exceptions.UnsupportedMediaType()

        try:
            return codec.decode(content, headers=headers)
        except exceptions.ParseError as exc:
            raise exceptions.BadRequest(str(exc))


class ValidatePathParamsComponent(Component):
    resolves_types = (ValidatedPathParams,)

    def resolve(self,
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


class ValidateQueryParamsComponent(Component):
    resolves_types = (ValidatedQueryParams,)

    def resolve(self,
                link: Link,
                query_params: http.QueryParams):
        query_fields = link.get_query_fields()

        validator = types.Object(
            properties=[
                (field.name, field.schema if field.schema else types.Any())
                for field in query_fields
            ],
            required=[field.name for field in query_fields if field.required]
        )

        try:
            query_params = validator.validate(query_params, allow_coerce=True)
        except types.ValidationError as exc:
            raise exceptions.BadRequest(exc.detail)
        return query_params


class ValidatedParamComponent(Component):
    resolves_types = (str, int, float, bool)

    def can_handle_parameter(self, parameter: inspect.Parameter):
        if parameter.annotation is parameter.empty:
            return True
        return parameter.annotation in self.resolves_types

    def resolve(self,
                parameter: inspect.Parameter,
                path_params: ValidatedPathParams,
                query_params: ValidatedQueryParams):
        params = path_params if (parameter.name in path_params) else query_params
        has_default = parameter.default is not parameter.empty

        param_validator = {
            parameter.empty: types.Any(),
            str: types.String(),
            int: types.Integer(),
            float: types.Number(),
            bool: types.Boolean()
        }[parameter.annotation]

        validator = types.Object(
            properties=[(parameter.name, param_validator)],
            required=[] if has_default else [parameter.name]
        )

        try:
            params = validator.validate(params, allow_coerce=True)
        except types.ValidationError as exc:
            raise exceptions.NotFound(exc.detail)
        return params.get(parameter.name, parameter.default)


VALIDATION_COMPONENTS = (
    RequestDataComponent(),
    ValidatePathParamsComponent(),
    ValidateQueryParamsComponent(),
    ValidatedParamComponent()
)
