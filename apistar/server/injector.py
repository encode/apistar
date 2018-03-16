import inspect

from apistar.exceptions import ConfigurationError


class Injector():
    def __init__(self, components, initial):
        self.components = components
        self.initial = initial
        self.reverse_initial = {
            val: key for key, val in initial.items()
        }
        self.resolver_cache = {}

    def resolve_function(self, func, output_name=None, seen_state=None, parent_parameter=None):
        if output_name is None:
            output_name = 'return'
        if seen_state is None:
            seen_state = set(self.initial)

        steps = []
        kwargs = {}
        consts = {}

        parameters = inspect.signature(func).parameters.values()
        for parameter in parameters:
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

        step = (func, kwargs, consts, output_name)
        steps.append(step)
        return steps

    def run(self, func, state):
        try:
            steps = self.resolver_cache[func]
        except KeyError:
            steps = self.resolve_function(func)
            self.resolver_cache[func] = steps

        for func, kwargs, consts, output_name in steps:
            func_kwargs = {key: state[val] for key, val in kwargs.items()}
            func_kwargs.update(consts)
            state[output_name] = func(**func_kwargs)

        return state['return']
