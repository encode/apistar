import inspect
import typing

from apistar import exceptions


class Component():
    def identity(self, parameter: inspect.Parameter):
        """
        Each component needs a unique identifier string that we use for lookups
        from the `state` dictionary when we run the dependency injection.
        """
        parameter_name = parameter.name.lower()
        annotation_name = parameter.annotation.__name__.lower()

        # If `resolve_parameter` includes `Parameter` then we use an identifier
        # that is additionally parameterized by the parameter name.
        args = inspect.signature(self.resolve).parameters.values()
        if inspect.Parameter in [arg.annotation for arg in args]:
            return annotation_name + ':' + parameter_name

        # Standard case is to use the class name, lowercased.
        return annotation_name

    def can_handle_parameter(self, parameter: inspect.Parameter):
        # Return `True` if this component can handle the given parameter.
        #
        # The default behavior is for components to handle whatever class
        # is used as the return annotation by the `resolve` method.
        #
        # You can override this for more customized styles, for example if you
        # wanted name-based parameter resolution, or if you want to provide
        # a value for a range of different types.
        #
        # Eg. Include the `Request` instance for any parameter named `request`.
        return_annotation = inspect.signature(self.resolve).return_annotation
        if return_annotation is inspect.Signature.empty:
            msg = (
                'Component "%s" must include a return annotation on the '
                '`resolve()` method, or override `can_handle_parameter`'
            )
            raise exceptions.ConfigurationError(msg % self.__class__.__name__)
        return parameter.annotation is return_annotation

    def resolve(self):
        raise NotImplementedError()


ReturnValue = typing.TypeVar('ReturnValue')
