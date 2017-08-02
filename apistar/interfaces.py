import abc
import typing

import coreapi

from apistar.routing import Routes

# WSGI

WSGIEnviron = typing.NewType('WSGIEnviron', dict)


# Settings

Settings = typing.NewType('Settings', dict)


# Routing

URLArgs = typing.NewType('URLArgs', dict)

Lookup = typing.Tuple[typing.Callable, typing.Dict[str, typing.Any]]


class Router(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def lookup(self, path: str, method: str) -> Lookup:
        raise NotImplementedError

    @abc.abstractmethod
    def reverse_url(self, identifier: str, values: dict=None) -> str:
        raise NotImplementedError

    @abc.abstractmethod
    def get_routes(self) -> Routes:
        raise NotImplementedError


# Schemas

Schema = coreapi.Document


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
