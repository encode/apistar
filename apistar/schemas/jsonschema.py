import typesystem

definitions = typesystem.SchemaDefinitions()

JSON_SCHEMA = (
    typesystem.Object(
        properties={
            "$ref": typesystem.String(),
            "type": typesystem.String() | typesystem.Array(items=typesystem.String()),
            "enum": typesystem.Array(unique_items=True, min_items=1),
            "definitions": typesystem.Object(
                additional_properties=typesystem.Reference(
                    "JSONSchema", definitions=definitions
                )
            ),
            # String
            "minLength": typesystem.Integer(minimum=0),
            "maxLength": typesystem.Integer(minimum=0),
            "pattern": typesystem.String(format="regex"),
            "format": typesystem.String(),
            # Numeric
            "minimum": typesystem.Number(),
            "maximum": typesystem.Number(),
            "exclusiveMinimum": typesystem.Number(),
            "exclusiveMaximum": typesystem.Number(),
            "multipleOf": typesystem.Number(exclusive_minimum=0),
            # Object
            "properties": typesystem.Object(
                additional_properties=typesystem.Reference(
                    "JSONSchema", definitions=definitions
                )
            ),
            "minProperties": typesystem.Integer(minimum=0),
            "maxProperties": typesystem.Integer(minimum=0),
            "patternProperties": typesystem.Object(
                additional_properties=typesystem.Reference(
                    "JSONSchema", definitions=definitions
                )
            ),
            "additionalProperties": (
                typesystem.Reference("JSONSchema", definitions=definitions)
                | typesystem.Boolean()
            ),
            "required": typesystem.Array(items=typesystem.String(), unique_items=True),
            # Array
            "items": (
                typesystem.Reference("JSONSchema", definitions=definitions)
                | typesystem.Array(
                    items=typesystem.Reference("JSONSchema", definitions=definitions),
                    min_items=1,
                )
            ),
            "additionalItems": (
                typesystem.Reference("JSONSchema", definitions=definitions)
                | typesystem.Boolean()
            ),
            "minItems": typesystem.Integer(minimum=0),
            "maxItems": typesystem.Integer(minimum=0),
            "uniqueItems": typesystem.Boolean(),
        }
    )
    | typesystem.Boolean()
)

definitions["JSONSchema"] = JSON_SCHEMA
