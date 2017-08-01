from apistar  import typesystem
import abc
import coreapi
import typing


# WSGI

WSGIEnviron = typing.NewType('WSGIEnviron', dict)


# Routing

URLArgs = typing.NewType('URLArgs', dict)
URLArg = typing.TypeVar('URLArg')

class PathWildcard(typesystem.String):
    allow_empty = True


Lookup = typing.Tuple[typing.Callable, typing.Dict[str, typing.Any]]
Route = typing.NamedTuple('Route', [('path', str), ('method', str), ('view', typing.Callable)])


class Router(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def lookup(self, path: str, method: str) -> Lookup:
        raise NotImplementedError

    @abc.abstractmethod
    def reverse_url(self, identifier: str, kwargs: dict=None) -> str:
        raise NotImplementedError

    @abc.abstractmethod
    def get_routes(self) -> typing.Sequence[Route]:
        raise NotImplementedError


# Schemas

Schema = typing.NewType('Schema', coreapi.Document)


# Templates

class Template(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def render(self, **context) -> str:
        raise NotImplementedError


class Templates(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def get_template(self, template_name: str) -> Template:
        raise NotImplementedError


# Statics

class StaticFile(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def get_response(self, environ):
        raise NotImplementedError


class StaticFiles(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def get_file(self, path: str) -> StaticFile:
        raise NotImplementedError

    @abc.abstractmethod
    def get_url(self, path: str) -> str:
        raise NotImplementedError


# Dependency Injection

ParamName = typing.NewType('ParamName', str)
ParamAnnotation = typing.NewType('ParamAnnotation', type)

class Injector(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def __init__(self,
                 providers: typing.Dict[type, typing.Callable],
                 required_state: typing.Dict[str, type]) -> None:
        raise NotImplementedError

    @abc.abstractmethod
    def run(self,
            func: typing.Callable,
            state: typing.Dict[str, typing.Any]) -> typing.Any:
        raise NotImplementedError
