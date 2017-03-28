class SchemaError(Exception):
    def __init__(self, schema, code):
        self.schema = schema
        self.code = code
        msg = schema.errors[code].format(**schema.__dict__)
        super().__init__(msg)
