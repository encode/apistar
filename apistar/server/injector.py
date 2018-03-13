from inspect import Parameter, signature

from apistar.exceptions import ConfigurationError


class Component():
    resolves = None

    def identity(self, parameter: Parameter):
        """
        Each component needs a unique identifier string that we use for lookups
        from the `state` dictionary when we run the dependency injection.
        """
        parameter_name = parameter.name.lower()
        annotation_name = parameter.annotation.__name__.lower()

        # If `resolve_parameter` includes `Parameter` then we use an identifier
        # that is additionally parameterized by the parameter name.
        args = signature(self.resolve_parameter).parameters.values()
        if Parameter in [arg.annotation for arg in args]:
            return annotation_name + ':' + parameter_name

        # Standard case is to use the class name, lowercased.
        return annotation_name

    def handle_parameter(self, parameter: Parameter):
        # Return `True` if this component can handle the given parameter.
        # The default behavior is for components to handle a particular
        # class or set of classes, however you could override this if you
        # wanted name-based parameter resolution.
        # Eg. Include the `Request` instance for any parameter named `request`.
        msg = 'Component %s must set "resolves" or override "handle_parameter"'
        assert self.resolves is not None, msg % self.__class__
        return parameter.annotation in self.resolves

    def resolve_parameter(self):
        raise NotImplementedError()


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

        parameters = signature(func).parameters.values()
        for parameter in parameters:
            # Check if the parameter class exists in 'initial'.
            if parameter.annotation in self.reverse_initial:
                initial_kwarg = self.reverse_initial[parameter.annotation]
                kwargs[parameter.name] = initial_kwarg
                continue

            # The 'Parameter' annotation can be used to get the parameter
            # itself. Used for example in 'Header' components that need the
            # parameter name in order to lookup a particular value.
            if parameter.annotation is Parameter:
                consts[parameter.name] = parent_parameter
                continue

            # Otherwise, find a component to resolve the parameter.
            for component in self.components:
                if component.handle_parameter(parameter):
                    identity = component.identity(parameter)
                    kwargs[parameter.name] = identity
                    if identity not in seen_state:
                        seen_state.add(identity)
                        steps += self.resolve_function(
                            func=component.resolve_parameter,
                            output_name=identity,
                            seen_state=seen_state,
                            parent_parameter=parameter
                        )
                    break
            else:
                msg = 'No component to handle parameter "%s" on function %s'
                raise ConfigurationError(msg % (parameter.name, func))

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
