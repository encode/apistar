import abc
import coreapi
import typing


# WSGI

WSGIEnviron = typing.NewType('WSGIEnviron', dict)


# HTTP Requests

Method = typing.NewType('Method', str)
Path = typing.NewType('Path', str)
Headers = typing.NewType('Headers', dict)
Header = typing.NewType('Header', str)
QueryParams = typing.NewType('QueryParams', dict)
QueryParam = typing.NewType('QueryParam', str)
Body = typing.NewType('Body', bytes)


# Routing

URLArgs = typing.NewType('URLArgs', dict)
URLArg = typing.TypeVar('URLArg')

Lookup = typing.Tuple[typing.Callable, typing.Dict[str, typing.Any]]
Route = typing.NamedTuple('Route', [('path', str), ('method', str), ('view', typing.Callable)])


class Router(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def lookup(self, path: str, method: str) -> Lookup:
        pass

    @abc.abstractmethod
    def reverse(self, identifier: str, kwargs: dict=None) -> str:
        pass

    @abc.abstractmethod
    def get_routes(self) -> typing.Sequence[Route]:
        pass


# Schemas

Schema = typing.NewType('Schema', coreapi.Document)


# Templates

class Template(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def render(self, **context) -> str:
        pass


class Templates(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def get_template(self, template_name: str) -> Template:
        pass


# Statics

class StaticFile(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def get_response(self, environ):
        pass


class StaticFiles(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def get_file(self, path: str) -> StaticFile:
        pass

    @abc.abstractmethod
    def get_url(self, path: str) -> str:
        pass


# Dependency Injection

ParamName = typing.NewType('ParamName', str)
ParamAnnotation = typing.NewType('ParamAnnotation', type)

class Injector(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def __init__(self,
                 providers: typing.Dict[type, typing.Callable],
                 required_state: typing.Dict[str, type]) -> None:
        pass

    @abc.abstractmethod
    def run(self,
            func: typing.Callable,
            state: typing.Dict[str, typing.Any]) -> typing.Any:
        pass
