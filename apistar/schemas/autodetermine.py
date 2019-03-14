import typesystem


class AutoDetermine(typesystem.Field):
    errors = {
        "not_an_object": "Must be an object.",
        "not_openapi_or_swagger": "Must include either an 'openapi' property or a 'swagger' property.",
        "both_openapi_and_swagger": "May not include both an 'openapi' property and a 'swagger' property.",
    }
    def validate(self, value, strict: bool=False):
        if not isinstance(value, dict):
            raise self.validation_error("not_an_object")

        if "openapi" in value and "swagger" not in value:
            return OPEN_API.validate(value, strict=strict)
        elif "swagger" in value and "openapi" not in value:
            return SWAGGER.validate(value, strict=strict)
        elif "openapi" in value and "swagger" in value:
            raise self.validation_error("both_openapi_and_swagger")
        raise self.validation_error("not_openapi_or_swagger")


AUTO_DETERMINE = AutoDetermine()
