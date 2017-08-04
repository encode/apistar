import inspect
import typing
from collections import OrderedDict
from contextlib import ExitStack

from apistar import exceptions, http, typesystem
from apistar.interfaces import (
    Injector, KeywordArgs, ParamAnnotation, ParamName, Resolver
)

Step = typing.NamedTuple('Step', [
    ('func', typing.Callable),
    ('input_keys', typing.Dict[str, str]),
    ('input_values', typing.Dict[str, str]),
    ('output_key', str),
    ('is_context_manager', bool)
])


class HTTPResolver(Resolver):
    def resolve(self, param: inspect.Parameter) -> typing.Optional[typing.Tuple[str, typing.Callable]]:
        annotation = param.annotation

        key = ''
        func = None  # type: typing.Callable

        if annotation is inspect.Parameter.empty:
            key = 'empty:' + param.name
            func = self.empty
            return (key, func)

        elif issubclass(annotation, (str, int, float, bool, typesystem.Boolean)):
            key = '%s:%s' % (annotation.__name__.lower(), param.name)
            func = self.scalar_type
            return (key, func)

        elif issubclass(annotation, (dict, list)):
            key = '%s:%s' % (annotation.__name__.lower(), param.name)
            func = self.container_type
            return (key, func)

        return None

    def empty(self,
              name: ParamName,
              kwargs: KeywordArgs,
              query_params: http.QueryParams):
        if name in kwargs:
            return kwargs[name]
        return query_params.get(name)

    def scalar_type(self,
                    name: ParamName,
                    kwargs: KeywordArgs,
                    query_params: http.QueryParams,
                    coerce: ParamAnnotation):
        if name in kwargs:
            value = kwargs[name]
            is_url_arg = True
        else:
            value = query_params.get(name)
            is_url_arg = False

        if value is None or isinstance(value, coerce):
            return value

        try:
            return coerce(value)
        except exceptions.TypeSystemError as exc:
            detail = {name: exc.detail}
        except (TypeError, ValueError) as exc:
            detail = {name: str(exc)}

        if is_url_arg:
            raise exceptions.NotFound()
        raise exceptions.ValidationError(detail=detail)

    def container_type(self,
                       data: http.RequestData,
                       coerce: ParamAnnotation):
        if data is None or isinstance(data, coerce):
            return data

        try:
            return coerce(data)
        except exceptions.TypeSystemError as exc:
            detail = exc.detail
        except (TypeError, ValueError) as exc:
            detail = str(exc)

        raise exceptions.ValidationError(detail=detail)


class CliResolver(Resolver):
    def resolve(self, param: inspect.Parameter) -> typing.Optional[typing.Tuple[str, typing.Callable]]:
        key = 'param:%s' % param.name
        func = self.command_line_argument
        return (key, func)

    def command_line_argument(self, name: ParamName, kwargs: KeywordArgs):
        return kwargs[name]


class DependencyInjector(Injector):
    """
    Stores all the state required in order to create
    dependency-injected functions.
    """
    def __init__(self,
                 components: typing.Dict[type, typing.Callable]=None,
                 initial_state: typing.Dict[type, typing.Any]=None,
                 required_state: typing.Dict[type, str]=None,
                 resolvers: typing.List[Resolver]=None) -> None:
        if components is None:
            components = {}  # pragma: nocover
        if initial_state is None:
            initial_state = {}  # pragma: nocover
        if required_state is None:
            required_state = {}  # pragma: nocover
        if resolvers is None:
            resolvers = []  # pragma: nocover

        self.components = components
        self.initial_state = initial_state
        self.required_state = required_state
        self.resolvers = resolvers

        self.setup_state = {
            cls.__name__.lower(): value
            for cls, value in initial_state.items()
        }
        self.steps = {}  # type: typing.Dict[typing.Callable, typing.List[Step]]

    def run(self,
            func: typing.Callable,
            state: typing.Dict[str, typing.Any]={}) -> typing.Any:
        try:
            steps = self.steps[func]
        except KeyError:
            steps = self.create_steps(func)
            self.steps[func] = steps

        state = {**state, **self.setup_state}

        ret = None
        with ExitStack() as stack:
            for step in steps:
                kwargs = {
                    argname: state[state_key]
                    for (argname, state_key) in step.input_keys.items()
                }
                kwargs.update(step.input_values)
                ret = step.func(**kwargs)
                if step.is_context_manager:
                    stack.enter_context(ret)
                state[step.output_key] = ret
            return ret

    def resolve(self, param: inspect.Parameter) -> typing.Tuple[str, typing.Optional[typing.Callable]]:
        annotation = param.annotation

        if annotation in self.components:
            key = annotation.__name__.lower()
            func = self.components[annotation]

            params = inspect.signature(func).parameters.values()
            if any([param.annotation is ParamName for param in params]):
                key += ':' + param.name

            return (key, func)

        elif annotation in self.initial_state:
            key = annotation.__name__.lower()
            func = None
            return (key, func)

        elif annotation in self.required_state:
            key = self.required_state[annotation]
            func = None
            return (key, func)

        for resolver in self.resolvers:
            ret = resolver.resolve(param)
            if ret is not None:
                return ret

        msg = 'Injector could not resolve parameter %s' % param
        raise exceptions.ConfigurationError(msg)

    def create_steps(self,
                     func: typing.Callable,
                     parent_param: typing.Optional[inspect.Parameter]=None,
                     seen_keys: typing.Set[str]=None) -> typing.List[Step]:
        """
        Return all the dependant steps required to run the given function.
        """
        if seen_keys is None:
            seen_keys = set()
        else:
            seen_keys = set(seen_keys)
        steps = []

        input_keys = OrderedDict()  # type: typing.Dict[str, str]
        input_values = OrderedDict()  # type: typing.Dict[str, str]

        # Add the steps required to satisfy each parameter in the function.
        for param in inspect.signature(func).parameters.values():
            if param.annotation is ParamName:
                input_values[param.name] = parent_param.name
                continue

            if param.annotation is ParamAnnotation:
                input_values[param.name] = parent_param.annotation
                continue

            key, provider_func = self.resolve(param)
            input_keys[param.name] = key
            if provider_func is None or (key in seen_keys):
                continue

            param_steps = self.create_steps(provider_func, param, seen_keys)
            steps.extend(param_steps)
            seen_keys |= set([
                step.output_key for step in param_steps
            ])

        # Add the step for the function itself.
        if parent_param is None:
            output_key = ''
            context_manager = False
        else:
            output_key, _ = self.resolve(parent_param)
            context_manager = is_context_manager(parent_param.annotation)

        step = Step(
            func=func,
            input_keys=input_keys,
            input_values=input_values,
            output_key=output_key,
            is_context_manager=context_manager
        )
        steps.append(step)
        return steps


def is_context_manager(cls: type):
    return hasattr(cls, '__enter__') and hasattr(cls, '__exit__')
