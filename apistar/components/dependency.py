import asyncio
import inspect
import typing
from contextlib import ExitStack

from apistar import exceptions, http, typesystem
from apistar.interfaces import Injector, Resolver
from apistar.types import KeywordArgs, ParamAnnotation, ParamName, ReturnValue

Step = typing.NamedTuple('Step', [
    ('func', typing.Callable),
    ('input_keys', typing.Dict[str, str]),
    ('input_values', typing.Dict[str, str]),
    ('output_key', str),
    ('is_context_manager', bool),
    ('is_async', bool)
])


def include_kwargs(step: Step,
                   kwargs: typing.Dict[str, typing.Any]={}):
    func, input_keys, input_values, output_key, is_context_manager, is_async = step
    input_values.update(kwargs)
    return Step(func, input_keys, input_values, output_key, is_context_manager, is_async)


class DependencyInjector(Injector):
    """
    Stores all the state required in order to handle running functions by
    dependency injecting parameters into the functions based on the state
    configured here.
    """

    def __init__(self,
                 components: typing.Dict[type, typing.Callable]=None,
                 initial_state: typing.Dict[type, typing.Any]=None,
                 required_state: typing.Dict[type, str]=None,
                 resolvers: typing.List[Resolver]=None) -> None:
        """
        Setup the dependency injection instance.

        Args:
            components: Map types onto functions that return them. These
                        functions themselves will be run using dependency
                        injection in order to provide each component.
            initial_state: Map types onto pre-provided values.
            required_state: Map types onto keys that must be provided on every
                            call to `run()` in the `state` dictionary.
            resolvers: A list of any custom resolvers, to handle any otherwise
                       unhandled type annotations.
        """
        if components is None:
            components = {}  # pragma: nocover
        if initial_state is None:
            initial_state = {}  # pragma: nocover
        if required_state is None:
            required_state = {}  # pragma: nocover
        if resolvers is None:
            resolvers = []  # pragma: nocover

        builtin = {ReturnValue: None, Injector: None}

        self.components = components
        self.initial_state = {**initial_state, **builtin}
        self.required_state = required_state
        self.resolvers = resolvers

        # Create a dictionary of any pre-existing state that should be
        # used on every call to `run()`.
        self._setup_state = {
            cls.__name__.lower(): value
            for cls, value in initial_state.items()
        }

        # Create a cache for storing the resolution of the required dependency
        # injection steps for any given function.
        self._steps_cache = {}  # type: typing.Dict[typing.Callable, typing.List[Step]]

    def run(self,
            func: typing.Callable,
            state: typing.Dict[str, typing.Any]={}) -> typing.Any:
        """
        Run a functions, using dependency inject to resolve any parameters
        that it requires.

        Args:
            func: The function to run.

        Returns:
            The return value of the function.
        """
        return self.run_all([func], state)

    def run_all(self,
                funcs: typing.List[typing.Callable],
                state: typing.Dict[str, typing.Any]={}) -> typing.Any:
        """
        Run some functions, using dependency inject to resolve any parameters
        that they require.

        Args:
            funcs: The functions to run.
            state: A dictionary of any per-call state that can differ on each
                   run. For example, this might include any base information
                   associated with an incoming HTTP request.

        Returns:
            The return value of the final function.
        """
        steps = []  # type: typing.List[Step]
        for func in funcs:
            try:
                # We cache the steps that are required to run a given function.
                func_steps = self._steps_cache[func]
            except KeyError:
                func_steps = self._create_steps(func)
                self._steps_cache[func] = func_steps
            steps += func_steps

        # Combine any preconfigured initial state with any explicit per-call state.
        state = {**self._setup_state, **state}

        ret = None
        with ExitStack() as stack:
            state['injector'] = BoundInjector(self, state, stack)
            for step in steps:
                if step.output_key in state and step.output_key != 'returnvalue':
                    continue

                # Keyword arguments are usually "input_key" references to state
                # that's been generated. In the case of `ParamName` or
                # `ParamAnnotation` they will be a pre-provided "input_value".
                kwargs = {
                    argname: state[state_key]
                    for (argname, state_key) in step.input_keys.items()
                }
                kwargs.update(step.input_values)

                # Run the function, possibly entering it into the context
                # stack in order to handle context managers.
                ret = step.func(**kwargs)
                if hasattr(ret, '__enter__') and hasattr(ret, '__exit__'):
                    ret = stack.enter_context(ret)
                state[step.output_key] = ret

        return ret

    async def run_async(self,
                        func: typing.Callable,
                        state: typing.Dict[str, typing.Any]={}) -> typing.Any:
        raise NotImplementedError('Cannot use `run_async` when running with WSGI.')

    async def run_all_async(self,
                            funcs: typing.List[typing.Callable],
                            state: typing.Dict[str, typing.Any]={}) -> typing.Any:
        raise NotImplementedError('Cannot use `run_all_async` when running with WSGI.')

    def _resolve_parameter(self,
                           param: inspect.Parameter,
                           func: typing.Callable) -> typing.Tuple[str, typing.Optional[typing.Callable]]:
        """
        Resolve a single function parameter, returning the information needed
        to inject it to the function.

        Args:
            param: A single function parameter.

        Returns:
            A tuple of the unique key to use for storing the state,
            and the function that will return the parameter value.
        """
        annotation = param.annotation

        if annotation in self.components:
            # If the type annotation is one of our components, then
            # use the function that is installed for creating that component.
            key = '%s:%d' % (annotation.__name__.lower(), id(annotation))
            func = self.components[annotation]

            params = inspect.signature(func).parameters.values()
            if any([param.annotation is ParamName for param in params]):
                key += ':' + param.name

            return (key, func)

        elif annotation in self.initial_state:
            # If the type annotation is in our initial state, then don't run
            # any function. We'll use the value for that initial state.
            key = annotation.__name__.lower()
            func = None
            return (key, func)

        elif annotation in self.required_state:
            # If the type annotation is marked as being required state, then
            # don't run any function. The value must be passed explicitly
            # in the `state` dictionary when calling `run()`.
            key = self.required_state[annotation]
            func = None
            return (key, func)

        for resolver in self.resolvers:
            # Try any custom resolvers that are installed.
            ret = resolver.resolve(param, func)
            if ret is not None:
                return ret

        msg = 'Injector could not resolve parameter %s' % param
        raise exceptions.CouldNotResolveDependency(msg)

    def _create_steps(self,
                      func: typing.Callable,
                      parent_param: typing.Optional[inspect.Parameter]=None,
                      seen_keys: typing.Set[str]=None) -> typing.List[Step]:
        """
        Return all the dependant steps required to run a given function.

        Args:
            func: The function that we want to run.
            parent_param: If the function is being used to resolve a parameter
                          on a later step, then that is included here.
            seen_keys: The set of any state keys that have already been resolved
                       in previous steps.

        Returns:
            A list of steps indicating all the functions to run in order to
            dependency inject the given function.
        """
        if seen_keys is None:
            seen_keys = set()
        else:
            seen_keys = set(seen_keys)
        steps = []

        input_keys = {}
        input_values = {}

        # Add the steps required to satisfy each parameter in the function.
        for param in inspect.signature(func).parameters.values():
            if param.annotation is ParamName:
                input_values[param.name] = parent_param.name
                continue

            if param.annotation is ParamAnnotation:
                input_values[param.name] = parent_param.annotation
                continue

            key, provider_func = self._resolve_parameter(param, func)
            input_keys[param.name] = key
            if provider_func is None or (key in seen_keys):
                continue

            param_steps = self._create_steps(provider_func, param, seen_keys)
            steps.extend(param_steps)
            seen_keys |= set([
                step.output_key for step in param_steps
            ])

        # Add the step for the function itself.
        if parent_param is None:
            output_key = 'returnvalue'
            context_manager = False
        else:
            output_key, _ = self._resolve_parameter(parent_param, None)
            context_manager = (
                hasattr(parent_param.annotation, '__enter__') and
                hasattr(parent_param.annotation, '__exit__')
            )

        step = Step(
            func=func,
            input_keys=input_keys,
            input_values=input_values,
            output_key=output_key,
            is_context_manager=context_manager,
            is_async=asyncio.iscoroutinefunction(func)
        )
        steps.append(step)
        return steps


class BoundInjector(Injector):
    """
    This injector is available to functions when running inside a dependency
    injected context. It is automatically provided by DependencyInjector.

    To use it, include the `Injector` component as an annotation in the
    function. For example:

    def my_function(injector: Injector):
        injector.run(some_function)
    """
    def __init__(self, bound_to, state, stack):
        self.bound_to = bound_to
        self.state = state
        self.stack = stack

    def run(self,
            func: typing.Callable,
            state: typing.Dict[str, typing.Any]={}) -> typing.Any:
        """
        Run a function, using dependency inject to resolve any parameters
        that it requires.

        Args:
            func: The function to run.

        Returns:
            The return value of the given function.
        """
        try:
            # We cache the steps that are required to run a given function.
            steps = self.bound_to._steps_cache[func]
        except KeyError:
            steps = self.bound_to._create_steps(func)
            self.bound_to._steps_cache[func] = steps

        self.state.update(state)

        ret = None

        for step in steps:
            if step.output_key in self.state and step.output_key != 'returnvalue':
                continue

            # Keyword arguments are usually "input_key" references to state
            # that's been generated. In the case of `ParamName` or
            # `ParamAnnotation` they will be a pre-provided "input_value".
            kwargs = {
                argname: self.state[state_key]
                for (argname, state_key) in step.input_keys.items()
            }
            kwargs.update(step.input_values)

            # Run the function, possibly entering it into the context
            # stack in order to handle context managers.
            ret = step.func(**kwargs)
            if hasattr(ret, '__enter__') and hasattr(ret, '__exit__'):
                ret = self.stack.enter_context(ret)
            self.state[step.output_key] = ret

        return ret

    def run_all(self,
                funcs: typing.List[typing.Callable],
                state: typing.Dict[str, typing.Any]={}) -> typing.Any:
        raise NotImplementedError(
            '.run_all() is not available in this context. '
            'Use .run() instead.'
        )

    async def run_async(self,
                        func: typing.Callable,
                        state: typing.Dict[str, typing.Any]={}) -> typing.Any:
        raise NotImplementedError('Cannot use `run_async` when running with WSGI.')

    async def run_all_async(self,
                            funcs: typing.List[typing.Callable],
                            state: typing.Dict[str, typing.Any]={}) -> typing.Any:
        raise NotImplementedError('Cannot use `run_all_async` when running with WSGI.')


# asyncio flavoured dependency injector...

class AsyncDependencyInjector(DependencyInjector):
    async def run_async(self,
                        func: typing.Callable,
                        state: typing.Dict[str, typing.Any]={}) -> typing.Any:
        """
        Run a function, using dependency inject to resolve any parameters
        that it requires.

        Args:
            func: The function to run.

        Returns:
            The return value of the given function.
        """
        return await self.run_all_async([func], state)

    async def run_all_async(self,
                            funcs: typing.List[typing.Callable],
                            state: typing.Dict[str, typing.Any]={}) -> typing.Any:
        """
        Run some functions, using dependency inject to resolve any parameters
        that they require.

        Args:
            funcs: The functions to run.
            state: A dictionary of any per-call state that can differ on each
                   run. For example, this might include any base information
                   associated with an incoming HTTP request.

        Returns:
            The return value of the final function.
        """
        steps = []  # type: typing.List[Step]
        for func in funcs:
            try:
                # We cache the steps that are required to run a given function.
                func_steps = self._steps_cache[func]
            except KeyError:
                func_steps = self._create_steps(func)
                self._steps_cache[func] = func_steps
            steps += func_steps

        # Combine any preconfigured initial state with any explicit per-call state.
        state = {**self._setup_state, **state}

        ret = None
        with ExitStack() as stack:
            state['injector'] = AsyncBoundInjector(self, state, stack)
            for step in steps:
                if step.output_key in state and step.output_key != 'returnvalue':
                    continue

                # Keyword arguments are usually "input_key" references to state
                # that's been generated. In the case of `ParamName` or
                # `ParamAnnotation` they will be a pre-provided "input_value".
                kwargs = {
                    argname: state[state_key]
                    for (argname, state_key) in step.input_keys.items()
                }
                kwargs.update(step.input_values)

                # Run the function, possibly entering it into the context
                # stack in order to handle context managers.
                if step.is_async:
                    ret = await step.func(**kwargs)
                else:
                    ret = step.func(**kwargs)

                if hasattr(ret, '__enter__') and hasattr(ret, '__exit__'):
                    ret = stack.enter_context(ret)
                state[step.output_key] = ret

        return ret


class AsyncBoundInjector(BoundInjector):
    """
    This injector is available to functions when running inside a dependency
    injected context. It is automatically provided by AsyncDependencyInjector.

    To use it, include the `Injector` component as an annotation in the
    function. For example:

    async def my_function(injector: Injector):
        await injector.run_async(some_function)
    """
    def __init__(self, bound_to, state, stack):
        self.bound_to = bound_to
        self.state = state
        self.stack = stack

    async def run_async(self,
                        func: typing.Callable,
                        state: typing.Dict[str, typing.Any]={}) -> typing.Any:
        """
        Run a function, using dependency inject to resolve any parameters
        that it requires.

        Args:
            func: The function to run.

        Returns:
            The return value of the given function.
        """
        try:
            # We cache the steps that are required to run a given function.
            steps = self.bound_to._steps_cache[func]
        except KeyError:
            steps = self.bound_to._create_steps(func)
            self.bound_to._steps_cache[func] = steps

        self.state.update(state)

        ret = None

        for step in steps:
            if step.output_key in self.state and step.output_key != 'returnvalue':
                continue

            # Keyword arguments are usually "input_key" references to state
            # that's been generated. In the case of `ParamName` or
            # `ParamAnnotation` they will be a pre-provided "input_value".
            kwargs = {
                argname: self.state[state_key]
                for (argname, state_key) in step.input_keys.items()
            }
            kwargs.update(step.input_values)

            # Run the function, possibly entering it into the context
            # stack in order to handle context managers.
            if step.is_async:
                ret = await step.func(**kwargs)
            else:
                ret = step.func(**kwargs)

            if hasattr(ret, '__enter__') and hasattr(ret, '__exit__'):
                ret = self.stack.enter_context(ret)
            self.state[step.output_key] = ret

        return ret

    async def run_all_async(self,
                            funcs: typing.List[typing.Callable],
                            state: typing.Dict[str, typing.Any]={}) -> typing.Any:
        raise NotImplementedError(
            '.run_all_async() is not available in this context. '
            'Use .run_async() instead.'
        )


# The Resolver subclasses below handle mapping annotations to component instances.

class CliResolver(Resolver):
    """
    Handles resolving parameters for running with the command line.
    """

    def resolve(self,
                param: inspect.Parameter,
                func: typing.Callable) -> typing.Optional[typing.Tuple[str, typing.Callable]]:
        """
        Resolve a single function parameter, returning the information needed
        to inject it to the function.

        Args:
            param: A single function parameter.

        Returns:
            A tuple of the unique key to use for storing the state,
            and the function that will return the parameter value.

            May return `None` if the parameter type is not handled
            by this resolver.
        """
        key = 'param:%s' % param.name
        func = self.command_line_argument
        return (key, func)

    def command_line_argument(self, name: ParamName, kwargs: KeywordArgs) -> typing.Any:
        """
        Provides a command line argument to a dependency injected parameter.

        Returns:
            The value that should be used for the handler function.
        """
        return kwargs[name]


class HTTPResolver(Resolver):
    """
    Handles resolving parameters for HTTP requests.
    """

    def resolve(self,
                param: inspect.Parameter,
                func: typing.Callable) -> typing.Optional[typing.Tuple[str, typing.Callable]]:
        """
        Resolve a single function parameter, returning the information needed
        to inject it to the function.

        Args:
            param: A single function parameter.

        Returns:
            A tuple of the unique key to use for storing the state,
            and the function that will return the parameter value.

            May return `None` if the parameter type is not handled
            by this resolver.
        """
        annotation = param.annotation

        key = ''
        default_func = None  # type: typing.Callable

        if annotation is inspect.Parameter.empty:
            key = 'empty:' + param.name
            default_func = self.empty

        elif issubclass(annotation, (str, int, float, bool, typesystem.Boolean)):
            key = '%s:%s' % (annotation.__name__.lower(), param.name)
            default_func = self.url_or_query_argument

        elif issubclass(annotation, (dict, list)):
            key = '%s:%s' % (annotation.__name__.lower(), param.name)
            default_func = self.body_argument

        else:
            return None

        # Allow a 'location' annotation on the function to override
        # the default function.
        locations = getattr(func, 'location', {})
        location = locations.get(param.name)
        if location is None:
            resolved_func = default_func  # type: typing.Callable
        else:
            location_to_func = {
                'query': self.query_argument,
                'form': self.form_argument,
                'body': self.body_argument,
                'url': self.url_argument
            }  # type: typing.Dict[str, typing.Callable]
            resolved_func = location_to_func[location]
        return (key, resolved_func)

    def empty(self,
              name: ParamName,
              kwargs: KeywordArgs,
              query_params: http.QueryParams) -> str:
        """
        Handles unannotated parameters for HTTP requests.
        These types use either a matched URL keyword argument, or else
        a query parameter.

        Args:
            name: The name of the parameter.
            kwargs: The URL keyword arguments, as returned by the router.
            query_params: The query parameters of the incoming HTTP request.

        Returns:
            The value that should be used for the handler function.
        """
        if name in kwargs:
            return kwargs[name]
        return query_params.get(name)

    def url_or_query_argument(self,
                              name: ParamName,
                              kwargs: KeywordArgs,
                              query_params: http.QueryParams,
                              coerce: ParamAnnotation) -> typing.Any:
        """
        Handles `str`, `int`, `float`, or `bool` annotations for HTTP requests.
        These types use either a matched URL keyword argument, or else
        a query parameter.

        Args:
            name: The name of the parameter.
            kwargs: The URL keyword arguments, as returned by the router.
            query_params: The query parameters of the incoming HTTP request.
            coerce: The type of the parameter.

        Returns:
            The value that should be used for the handler function.
        """
        if name in kwargs:
            return self.url_argument(name, kwargs, coerce)
        return self.query_argument(name, query_params, coerce)

    def url_argument(self,
                     name: ParamName,
                     kwargs: KeywordArgs,
                     coerce: ParamAnnotation) -> typing.Any:
        value = kwargs[name]
        if value is None or isinstance(value, coerce):
            return value

        try:
            return coerce(value)
        except exceptions.TypeSystemError as exc:
            detail = {name: exc.detail}
        except (TypeError, ValueError) as exc:
            detail = {name: str(exc)}

        raise exceptions.NotFound(detail=detail)

    def query_argument(self,
                       name: ParamName,
                       query_params: http.QueryParams,
                       coerce: ParamAnnotation) -> typing.Any:
        value = query_params.get(name)
        if value is None or isinstance(value, coerce):
            return value

        try:
            return coerce(value)
        except exceptions.TypeSystemError as exc:
            detail = {name: exc.detail}
        except (TypeError, ValueError) as exc:
            detail = {name: str(exc)}
        raise exceptions.ValidationError(detail=detail)

    def form_argument(self,
                      data: http.RequestData,
                      name: ParamName,
                      coerce: ParamAnnotation) -> typing.Any:
        if not isinstance(data, dict):
            raise exceptions.ValidationError(
                detail='Request data must be an object.'
            )

        data = data.get(name)
        if data is None or isinstance(data, coerce):
            return data

        try:
            return coerce(data)
        except exceptions.TypeSystemError as exc:
            detail = exc.detail
        except (TypeError, ValueError) as exc:
            detail = str(exc)

        raise exceptions.ValidationError(detail=detail)

    def body_argument(self,
                      data: http.RequestData,
                      coerce: ParamAnnotation) -> typing.Any:
        if data is None or isinstance(data, coerce):
            return data

        try:
            return coerce(data)
        except exceptions.TypeSystemError as exc:
            detail = exc.detail
        except (TypeError, ValueError) as exc:
            detail = str(exc)

        raise exceptions.ValidationError(detail=detail)
