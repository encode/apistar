from apistar.interfaces import Injector, URLArgs, QueryParams, ParamName, ParamAnnotation
import functools
import inspect
import typing
from collections import OrderedDict
from contextlib import ExitStack


Step = typing.NamedTuple('Step', [
    ('func', typing.Callable),
    ('input_keys', typing.Dict[str, str]),
    ('input_values', typing.Dict[str, str]),
    ('output_key', str),
    ('is_context_manager', bool)
])

DependencyResolution = typing.Tuple[str, typing.Optional[typing.Callable]]


def empty(name: ParamName, args: URLArgs, queryparams: QueryParams):
    if name in args:
        return args[name]
    return queryparams.get(name)


def typed(name: ParamName, args: URLArgs, queryparams: QueryParams, coerce: ParamAnnotation):
    if name in args:
        return args[name]

    value = queryparams.get(name)
    if value is None or isinstance(value, coerce):
        return value

    try:
        return coerce(value)
    except (TypeError, ValueError):
        return None


class DependencyInjector(Injector):
    """
    Stores all the state required in order to create
    dependency-injected functions.
    """

    def __init__(self,
                 providers: typing.Dict[type, typing.Callable]=None,
                 required_state: typing.Dict[str, type]=None) -> None:
        if providers is None:
            providers = {}
        if required_state is None:
            required_state = {}

        self.providers = providers
        self.required_state = required_state
        self.required_state_lookup = {
            cls: key for key, cls in required_state.items()
        }
        self.steps = {}  # type: typing.Dict[typing.Callable, typing.List[Step]]

    def run(self,
            func: typing.Callable,
            state: typing.Dict[str, typing.Any]=None) -> typing.Any:
        if state is None:
            state = {}

        try:
            steps = self.steps[func]
        except KeyError:
            steps = self.create_steps(func)
            self.steps[func] = steps

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

    def resolve(self, param: inspect.Parameter) -> DependencyResolution:
        if param.annotation in self.required_state_lookup:
            key = self.required_state_lookup[param.annotation]
            func = None
            return (key, func)

        elif param.annotation in self.providers:
            key = param.annotation.__name__.lower()
            func = self.providers[param.annotation]

            params = inspect.signature(func).parameters.values()
            if any([param.annotation is ParamName for param in params]):
                key += ':' + param.name

            return (key, func)

        elif param.annotation is inspect.Parameter.empty:
            key = 'empty:' + param.name
            func = empty
            return (key, func)

        elif param.annotation in (str, int, float, bool):
            key = f'{param.annotation.__name__}:{param.name}'
            func = typed
            return (key, func)

        raise Exception('Injector could not resolve parameter %s' % param)

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
