from typing import Callable


def exclude_from_schema(func: Callable) -> Callable:
    func.exclude_from_schema = True  # type: ignore
    return func
