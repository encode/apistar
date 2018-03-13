# from apistar.server.core import Component
#
#
# class ValidatedQueryParamsComponent(Component):
#     ...
#
#
# class ValidatedBodyParamComponent(Component):
#     ...
#
#
# class PrimitiveDataTypes(Component):
#     resolves = (int, float, str, bool)
#
#     def resolve_parameter(self, parameter: inspect.Parameter, path_params: ValidatedPathParams, query_params: ValidatedQueryParams):
#         name = parameter.name
#         ...
#
#
# class CompoundDataTypes(Component):
#     resolves = (list, dict)
#
#     def resolve_parameter(self, parameter: inspect.Parameter, body_param: ValidatedBodyParam):
#         name = parameter.name
#         ...
#
#
# def validate(link: Link, path_params: PathParams, query_params: QueryParams):
#     items = {}
#     required = []
#     for field in link.path_fields:
#         if field.schema is None:
#             items[field.name] = types.Any()
#         else
#             items[field.name] = field.schema
#         required.append(field.name)
#     validator = types.Object(items=items, required=required, additional_items=False)
#     # ...
#
#     items = {}
#     required = []
#     for field in query_params:
#         if field.schema is None:
#             items[field.name] = types.Any()
#         else
#             items[field.name] = field.schema
#         if field.required:
#             required.append(field.name)
#     validator = types.Object(items=items, required=required, additional_items=False)
#     # ...
