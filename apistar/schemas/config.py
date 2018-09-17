from apistar import validators

# from apistar.validate import validate_yaml

APISTAR_CONFIG = validators.Object(
    properties=[
        ('schema', validators.Object(
            properties=[
                ('path', validators.String()),
                ('format', validators.String(enum=['openapi', 'swagger'])),
            ],
            additional_properties=False,
            required=['path', 'format']
        )),
        ('docs', validators.Object(
            properties=[
                ('theme', validators.String(enum=['apistar', 'redoc', 'swaggerui'])),
            ],
            additional_properties=False,
        ))
    ],
    additional_properties=False,
    required=['schema'],
)
#
#
# class ConfigSchema:
#     def decode(self, content, **options):
#         return validate_yaml(content, validator=APISTAR_CONFIG)
