import collections
import typing


class Route(collections.abc.Iterable):
    def __init__(self,
                 path: str,
                 method: str,
                 view: typing.Callable,
                 name: str=None) -> None:
        self.path = path
        self.method = method
        self.view = view
        if name is None:
            self.name = view.__name__
        else:
            self.name = name

    def __iter__(self) -> typing.Iterator:
        return iter((self.path, self.method, self.view, self.name))


class Include(collections.abc.Iterable):
    def __init__(self,
                 path: str,
                 routes: typing.Sequence[typing.Union[Route, 'Include']],
                 namespace: str=None) -> None:
        self.path = path
        self.routes = routes
        self.namespace = namespace

    def __iter__(self) -> typing.Iterator:
        return iter((self.path, self.routes, self.namespace))


class Command(collections.abc.Iterable):
    def __init__(self,
                 name: str,
                 handler: typing.Callable) -> None:
        self.name = name
        self.handler = handler

    def __iter__(self) -> typing.Iterator:
        return iter((self.name, self.handler))


class Component(collections.abc.Iterable):
    def __init__(self,
                 cls: type,
                 init: typing.Callable=None,
                 preload: bool=True) -> None:
        self.cls = cls
        if init is not None:
            self.init = init
        else:
            self.init = cls  # type: ignore
        self.preload = preload

    def __iter__(self) -> typing.Iterator:
        return iter((self.cls, self.init, self.preload))


def flatten_routes(routes: typing.Sequence[typing.Union[Route, Include]],
                   path_prefix: str=None,
                   namespace_prefix: str=None) -> typing.Sequence[Route]:
    if path_prefix is None:
        path_prefix = ''
    if namespace_prefix is None:
        namespace_prefix = ''

    flattened_routes = []
    for item in routes:
        if isinstance(item, Route):
            path, method, view, name = item
            path = path_prefix + path
            name = namespace_prefix + name
            route = Route(path, method, view, name)
            flattened_routes.append(route)
        elif isinstance(item, Include):
            path, routes, namespace = item
            includes_path_prefix = path_prefix + path
            if namespace is not None:
                includes_namespace_prefix = namespace_prefix + namespace + ':'
            else:
                includes_namespace_prefix = namespace_prefix
            for route in flatten_routes(
                    routes, includes_path_prefix, includes_namespace_prefix):
                flattened_routes.append(route)

    return flattened_routes


def annotate(**kwargs):
    def decorator(func):
        nonlocal kwargs
        for key, value in kwargs.items():
            setattr(func, key, value)
        return func
    return decorator
