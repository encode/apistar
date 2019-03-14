import typesystem

APISTAR_CONFIG = typesystem.Object(
    properties={
        "schema": typesystem.Object(
            properties={
                "path": typesystem.String(),
                "format": typesystem.Choice(choices=["openapi", "swagger"]),
                "base_format": typesystem.Choice(choices=["json", "yaml"]),
            },
            additional_properties=False,
            required=["path", "format"],
        ),
        "docs": typesystem.Object(
            properties={
                "output_dir": typesystem.String(),
                "theme": typesystem.Choice(choices=["apistar", "redoc", "swaggerui"]),
            },
            additional_properties=False,
        ),
    },
    additional_properties=False,
    required=["schema"],
)
