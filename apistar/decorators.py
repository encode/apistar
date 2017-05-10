def exclude_from_schema(func):
    func.exclude_from_schema = True  # type: ignore
    return func
