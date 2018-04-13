import asyncio
import inspect

from apistar.exceptions import ConfigurationError


class BaseInjector():
    def run(self, func, state):
        raise NotImplementedError()


class Injector(BaseInjector):
    allow_async = False

    def __init__(self, components, initial):
        self.components = components
        self.initial = initial
        self.reverse_initial = {
            val: key for key, val in initial.items()
        }
        self.resolver_cache = {}

    def resolve_function(self, func, output_name=None, seen_state=None, parent_parameter=None):
        if output_name is None:
            output_name = 'response'

        if seen_state is None:
            seen_state = set(self.initial)

        steps = []
        kwargs = {}
        consts = {}

        parameters = inspect.signature(func).parameters.values()
        for parameter in parameters:
            # The 'response' keyword always indicates the previous return value.
            if parameter.name == 'response':
                kwargs['response'] = 'response'
                continue

            # Check if the parameter class exists in 'initial'.
            if parameter.annotation in self.reverse_initial:
                initial_kwarg = self.reverse_initial[parameter.annotation]
                kwargs[parameter.name] = initial_kwarg
                continue

            # The 'Parameter' annotation can be used to get the parameter
            # itself. Used for example in 'Header' components that need the
            # parameter name in order to lookup a particular value.
            if parameter.annotation is inspect.Parameter:
                consts[parameter.name] = parent_parameter
                continue

            # Otherwise, find a component to resolve the parameter.
            for component in self.components:
                if component.can_handle_parameter(parameter):
                    identity = component.identity(parameter)
                    kwargs[parameter.name] = identity
                    if identity not in seen_state:
                        seen_state.add(identity)
                        steps += self.resolve_function(
                            func=component.resolve,
                            output_name=identity,
                            seen_state=seen_state,
                            parent_parameter=parameter
                        )
                    break
            else:
                msg = 'No component able to handle parameter "%s" on function "%s".'
                raise ConfigurationError(msg % (parameter.name, func.__name__))

        is_async = asyncio.iscoroutinefunction(func)
        if is_async and not self.allow_async:
            msg = 'Function "%s" may not be async.'
            raise ConfigurationError(msg % (func.__name__, ))

        step = (func, is_async, kwargs, consts, output_name)
        steps.append(step)
        return steps

    def resolve_functions(self, funcs):
        steps = []
        seen_state = set(self.initial)
        for func in funcs:
            func_steps = self.resolve_function(func, seen_state=seen_state)
            steps.extend(func_steps)
        return steps

    def run(self, funcs, state):
        funcs = tuple(funcs)
        try:
            steps = self.resolver_cache[funcs]
        except KeyError:
            steps = self.resolve_functions(funcs)
            self.resolver_cache[funcs] = steps

        for func, is_async, kwargs, consts, output_name in steps:
            func_kwargs = {key: state[val] for key, val in kwargs.items()}
            func_kwargs.update(consts)
            state[output_name] = func(**func_kwargs)

        return state['response']


class ASyncInjector(Injector):
    allow_async = True

    async def run_async(self, funcs, state):
        funcs = tuple(funcs)
        try:
            steps = self.resolver_cache[funcs]
        except KeyError:
            steps = self.resolve_functions(funcs)
            self.resolver_cache[funcs] = steps

        for func, is_async, kwargs, consts, output_name in steps:
            func_kwargs = {key: state[val] for key, val in kwargs.items()}
            func_kwargs.update(consts)
            if is_async:
                state[output_name] = await func(**func_kwargs)
            else:
                state[output_name] = func(**func_kwargs)

        return state['response']
