from apistar import validators

APISTAR_CONFIG = validators.Object(
    properties=[
        ('schema', validators.Object(
            properties=[
                ('path', validators.String()),
                ('format', validators.String(enum=['openapi', 'swagger'])),
                ('base_format', validators.String(enum=['json', 'yaml'])),
            ],
            additional_properties=False,
            required=['path', 'format']
        )),
        ('docs', validators.Object(
            properties=[
                ('output_dir', validators.String()),
                ('theme', validators.String(enum=['apistar', 'redoc', 'swaggerui'])),
            ],
            additional_properties=False,
        ))
    ],
    additional_properties=False,
    required=['schema'],
)
