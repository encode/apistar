import abc
import inspect
import typing

import coreapi

from apistar import cli, routing

# Common

KeywordArgs = typing.Dict[str, typing.Any]
HandlerLookup = typing.Tuple[typing.Callable, KeywordArgs]


# WSGI

WSGIEnviron = typing.NewType('WSGIEnviron', dict)


# Settings

Settings = typing.NewType('Settings', dict)


# Routing

RouteConfig = typing.Sequence[typing.Union[routing.Route, routing.Include]]
RouteConfig.__name__ = 'RouteConfig'


class Router(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def lookup(self, path: str, method: str) -> HandlerLookup:
        raise NotImplementedError

    @abc.abstractmethod
    def reverse_url(self, identifier: str, values: dict=None) -> str:
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


# Command Line Parser

CommandConfig = typing.Sequence[cli.Command]
CommandConfig.__name__ = 'CommandConfig'


class CommandLineClient(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def __init__(self,
                 commands: CommandConfig) -> None:
        raise NotImplementedError

    @abc.abstractmethod
    def parse(self,
              args: typing.Sequence[str]) -> HandlerLookup:
        raise NotImplementedError


# Dependency Injection

ParamName = typing.NewType('ParamName', str)
ParamAnnotation = typing.NewType('ParamAnnotation', type)


class Resolver(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def resolve(self, param: inspect.Parameter) -> typing.Optional[typing.Tuple[str, typing.Callable]]:
        raise NotImplementedError


class Injector(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def __init__(self,
                 components: typing.Dict[type, typing.Callable],
                 initial_state: typing.Dict[str, typing.Any],
                 required_state: typing.Dict[str, type],
                 resolvers: typing.List[Resolver]) -> None:
        raise NotImplementedError

    @abc.abstractmethod
    def run(self,
            func: typing.Callable,
            state: typing.Dict[str, typing.Any]) -> typing.Any:
        raise NotImplementedError


# Console

class Console(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def echo(self, message: str) -> None:
        raise NotImplementedError


# App

class App(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def main(self, args: typing.Sequence[str]=None) -> None:
        raise NotImplementedError
