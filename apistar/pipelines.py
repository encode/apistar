from collections import namedtuple
import inspect
import re


Func = namedtuple('Func', ('function', 'inputs', 'output'))
Input = namedtuple('Input', ('argname', 'statename'))

first_cap_re = re.compile('(.)([A-Z][a-z]+)')
all_cap_re = re.compile('([a-z0-9])([A-Z])')


def get_class_id(cls):
    # http://stackoverflow.com/questions/1175208/elegant-python-function-to-convert-camelcase-to-snake-case
    if cls is None:
        return ''
    name = cls.__name__
    s1 = first_cap_re.sub(r'\1_\2', name)
    return all_cap_re.sub(r'\1_\2', s1).lower()


def get_func(function):
    """
    Given a function which is fully type-annotated,
    returns a `Func` instance, describing the type information.
    """
    inputs = tuple([
        Input(argname, get_class_id(input_type))
        for argname, input_type in get_input_types(function)
    ])
    output = get_class_id(get_output_type(function))
    return Func(function, inputs, output)



def get_input_types(function):
    if type(function) == type:
        # Class()
        annotations = function.__init__.__annotations__
        argnames = inspect.getfullargspec(function.__init__)[0][1:]
    elif hasattr(function, '__self__'):
        # @classmethod
        annotations = function.__annotations__
        argnames = inspect.getfullargspec(function)[0][1:]
    else:
        # Plain function
        annotations = function.__annotations__
        argnames = inspect.getfullargspec(function)[0]

    return [
        (argname, annotations[argname])
        for argname in argnames
    ]


def get_output_type(function):
    if type(function) == type:
        # Class()
        return function
    elif hasattr(function, '__self__'):
        # @classmethod
        return function.__self__
    # Plain function
    return function.__annotations__['return']


def _build_pipeline(function, initial_types=None):
    pipeline = []
    seen_types = set(initial_types or [])

    # Add all the function's input requirements to the pipeline
    for argname, required_type in get_input_types(function):
        if required_type in seen_types:
            continue
        this_function = getattr(required_type, 'build')
        this_pipeline, this_seen_types = _build_pipeline(this_function, seen_types)
        pipeline.extend(this_pipeline)
        seen_types |= this_seen_types

    # Add the function itself to the pipeline
    func = get_func(function)
    output_type = get_output_type(function)

    pipeline.append(func)
    if output_type is not None:
        seen_types.add(output_type)

    return (pipeline, seen_types)


def build_pipeline(function, initial_types=None, required_type=None):
    """
    Return a Pipeline instance.
    """
    pipeline, seen_types = _build_pipeline(function, initial_types)
    if (required_type is not None) and (required_type not in seen_types):
        function = getattr(required_type, 'build')
        final_pipeline, seen_types = _build_pipeline(function, seen_types)
        pipeline.extend(final_pipeline)
    return pipeline
