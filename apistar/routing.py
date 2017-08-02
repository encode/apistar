import collections
import typing

from apistar import typesystem

URLArgs = typing.NewType('URLArgs', dict)


class Route(collections.abc.Iterable):
    def __init__(self,
                 path: str,
                 method: str,
                 view: typing.Callable, name: str=None) -> None:
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


Routes = typing.Sequence[typing.Union[Route, Include]]


def flatten_routes(routes: Routes,
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
            path_prefix += path
            if namespace is not None:
                namespace_prefix += namespace + ':'
            for route in flatten_routes(routes, path_prefix, namespace_prefix):
                flattened_routes.append(route)

    return flattened_routes


class PathWildcard(typesystem.String):
    pass
