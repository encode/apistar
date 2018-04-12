import inspect
import typing

from apistar import codecs, exceptions, http, types, validators
from apistar.conneg import negotiate_content_type
from apistar.server.components import Component
from apistar.server.core import Route

ValidatedPathParams = typing.NewType('ValidatedPathParams', dict)
ValidatedQueryParams = typing.NewType('ValidatedQueryParams', dict)
ValidatedRequestData = typing.TypeVar('ValidatedRequestData')


class RequestDataComponent(Component):
    def __init__(self):
        self.codecs = [
            codecs.JSONCodec(),
            codecs.URLEncodedCodec(),
            codecs.MultiPartCodec(),
        ]

    def can_handle_parameter(self, parameter: inspect.Parameter):
        return parameter.annotation is http.RequestData

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
    def resolve(self,
                route: Route,
                path_params: http.PathParams) -> ValidatedPathParams:
        path_fields = route.link.get_path_fields()

        validator = validators.Object(
            properties=[
                (field.name, field.schema if field.schema else validators.Any())
                for field in path_fields
            ],
            required=[field.name for field in path_fields]
        )

        try:
            path_params = validator.validate(path_params, allow_coerce=True)
        except validators.ValidationError as exc:
            raise exceptions.NotFound(exc.detail)
        return ValidatedPathParams(path_params)


class ValidateQueryParamsComponent(Component):
    def resolve(self,
                route: Route,
                query_params: http.QueryParams) -> ValidatedQueryParams:
        query_fields = route.link.get_query_fields()

        validator = validators.Object(
            properties=[
                (field.name, field.schema if field.schema else validators.Any())
                for field in query_fields
            ],
            required=[field.name for field in query_fields if field.required]
        )

        try:
            query_params = validator.validate(query_params, allow_coerce=True)
        except validators.ValidationError as exc:
            raise exceptions.BadRequest(exc.detail)
        return ValidatedQueryParams(query_params)


class ValidateRequestDataComponent(Component):
    def can_handle_parameter(self, parameter: inspect.Parameter):
        return parameter.annotation is ValidatedRequestData

    def resolve(self,
                route: Route,
                data: http.RequestData):
        body_field = route.link.get_body_field()

        if not body_field or not body_field.schema:
            return data

        validator = body_field.schema

        try:
            return validator.validate(data, allow_coerce=True)
        except validators.ValidationError as exc:
            raise exceptions.BadRequest(exc.detail)


class PrimitiveParamComponent(Component):
    def can_handle_parameter(self, parameter: inspect.Parameter):
        return parameter.annotation in (str, int, float, bool, parameter.empty)

    def resolve(self,
                parameter: inspect.Parameter,
                path_params: ValidatedPathParams,
                query_params: ValidatedQueryParams):
        params = path_params if (parameter.name in path_params) else query_params
        has_default = parameter.default is not parameter.empty
        allow_null = parameter.default is None

        param_validator = {
            parameter.empty: validators.Any(),
            str: validators.String(allow_null=allow_null),
            int: validators.Integer(allow_null=allow_null),
            float: validators.Number(allow_null=allow_null),
            bool: validators.Boolean(allow_null=allow_null)
        }[parameter.annotation]

        validator = validators.Object(
            properties=[(parameter.name, param_validator)],
            required=[] if has_default else [parameter.name]
        )

        try:
            params = validator.validate(params, allow_coerce=True)
        except validators.ValidationError as exc:
            raise exceptions.NotFound(exc.detail)
        return params.get(parameter.name, parameter.default)


class CompositeParamComponent(Component):
    def can_handle_parameter(self, parameter: inspect.Parameter):
        return issubclass(parameter.annotation, types.Type)

    def resolve(self,
                parameter: inspect.Parameter,
                data: ValidatedRequestData):
        try:
            return parameter.annotation(data)
        except validators.ValidationError as exc:
            raise exceptions.BadRequest(exc.detail)


VALIDATION_COMPONENTS = (
    RequestDataComponent(),
    ValidatePathParamsComponent(),
    ValidateQueryParamsComponent(),
    ValidateRequestDataComponent(),
    PrimitiveParamComponent(),
    CompositeParamComponent()
)
