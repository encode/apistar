from collections import namedtuple
import inspect
import re


Func = namedtuple('Func', ('function', 'inputs', 'output', 'input_types', 'output_type'))
Input = namedtuple('Input', ('argname', 'requirement'))

first_cap_re = re.compile('(.)([A-Z][a-z]+)')
all_cap_re = re.compile('([a-z0-9])([A-Z])')


def get_class_id(cls):
    # http://stackoverflow.com/questions/1175208/elegant-python-function-to-convert-camelcase-to-snake-case
    name = cls.__name__
    s1 = first_cap_re.sub(r'\1_\2', name)
    return all_cap_re.sub(r'\1_\2', s1).lower()


def get_argnames(callable_object):
    return inspect.getfullargspec(callable_object)[0]


def get_func(function_or_class):
    """
    Given a function which is fully type-annotated,
    returns a `Func` instance, describing the type information.
    """
    if type(function_or_class) == type:
        # class
        annotations = getattr(function_or_class.__init__, '__annotations__', {})
        argnames = get_argnames(function_or_class.__init__)[1:]
        output = get_class_id(function_or_class)
        output_type = function_or_class
    elif hasattr(function_or_class, '__self__'):
        # classmethod
        annotations = function_or_class.__annotations__
        argnames = get_argnames(function_or_class)[1:]
        output = get_class_id(function_or_class.__self__)
        output_type = function_or_class.__self__
    else:
        # plain function
        annotations = function_or_class.__annotations__
        argnames = get_argnames(function_or_class)
        output = get_class_id(annotations['return'])
        output_type = annotations['return']

    inputs = tuple(
        Input(argname, get_class_id(annotations[argname]))
        for argname in argnames
    )
    input_types = [annotations[argname] for argname in argnames]
    return Func(function_or_class, inputs, output, input_types, output_type)


def build_pipeline(functions, required, initial):
    """
    Return a list of `Func` instances that can be run sequentially
    in order to fulfil the given type requirement.
    """
    provided_by = {}
    for function in functions:
        func = get_func(function)
        provided_by[func.output] = func

    requirements = set([get_class_id(required)])
    seen = set([get_class_id(cls) for cls in initial])
    pipeline = []

    while requirements:
        for requirement in list(requirements):
            func = provided_by[requirement]
            pipeline.append(func)
            new_requirements = set([requirement for (argname, requirement) in func.inputs])
            seen |= set([requirement])
            requirements = (requirements | new_requirements) - seen

    return tuple(reversed(pipeline))


def build_function_pipeline(functions, initial):
    """
    Return a list of `Func` instances to run the given functions.
    """
    seen = set(initial)
    pipeline = []

    for function in functions:
        func = get_func(function)
        required_types = func.input_types
        output_type = func.output_type

        for required_type in required_types:
            if required_type in seen:
                continue
            build_function = getattr(required_type, 'build', required_type)
            this_pipeline, this_seen = build_function_pipeline([build_function], seen)
            pipeline.extend(this_pipeline)
            seen |= this_seen

        pipeline.append(func)
        if output_type is not None:
            seen |= set([output_type])

    return (pipeline, seen)
