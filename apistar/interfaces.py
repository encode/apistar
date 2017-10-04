"""
Component interfaces, as abstract base classes.

These interfaces my be used as type annotations in handler methods.
"""
import abc
import inspect
import typing

import coreapi

from apistar import http
from apistar.types import HandlerLookup


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

class FileWrapper(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def __call__(self, file: typing.Any) -> typing.Iterable:
        raise NotImplementedError


class StaticFile(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def get_response(self, method: http.Method, headers: http.Headers, file_wrapper: FileWrapper):
        raise NotImplementedError


class StaticFiles(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def get_file(self, path: str) -> StaticFile:
        raise NotImplementedError

    @abc.abstractmethod
    def get_url(self, path: str) -> str:
        raise NotImplementedError


# Sessions

class SessionStore(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def new(self) -> http.Session:
        raise NotImplementedError

    @abc.abstractmethod
    def load(self, session_id: str) -> http.Session:
        raise NotImplementedError

    @abc.abstractmethod
    def save(self, session: http.Session) -> typing.Dict[str, str]:
        raise NotImplementedError


# Authentication

class Auth(metaclass=abc.ABCMeta):
    user = None  # type: typing.Any
    token = None  # type: typing.Any

    @abc.abstractmethod
    def is_authenticated(self) -> bool:
        raise NotImplementedError

    @abc.abstractmethod
    def get_display_name(self) -> typing.Optional[str]:
        raise NotImplementedError

    @abc.abstractmethod
    def get_user_id(self) -> typing.Optional[str]:
        raise NotImplementedError


# Command Line Parser

class CommandLineClient(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def parse(self,
              args: typing.Sequence[str]) -> HandlerLookup:
        raise NotImplementedError


# Dependency Injection

class Resolver(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def resolve(self,
                param: inspect.Parameter,
                func: typing.Callable) -> typing.Optional[typing.Tuple[str, typing.Callable]]:
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
            state: typing.Dict[str, typing.Any]={}) -> typing.Any:
        raise NotImplementedError

    @abc.abstractmethod
    def run_all(self,
                funcs: typing.List[typing.Callable],
                state: typing.Dict[str, typing.Any]={}) -> typing.Any:
        raise NotImplementedError

    @abc.abstractmethod
    async def run_async(self,
                        func: typing.Callable,
                        state: typing.Dict[str, typing.Any]={}) -> typing.Any:
        raise NotImplementedError

    @abc.abstractmethod
    async def run_all_async(self,
                            funcs: typing.List[typing.Callable],
                            state: typing.Dict[str, typing.Any]={}) -> typing.Any:
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

    @abc.abstractmethod
    def reverse_url(self, identifier: str, **values) -> str:
        raise NotImplementedError

    @abc.abstractmethod
    def render_template(self, template_name: str, **context) -> str:
        raise NotImplementedError
