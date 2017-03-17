from collections import namedtuple
import inspect
import re


Func = namedtuple('Func', ('function', 'inputs', 'output'))
Input = namedtuple('Input', ('argname', 'statename', 'subname'))

first_cap_re = re.compile('(.)([A-Z][a-z]+)')
all_cap_re = re.compile('([a-z0-9])([A-Z])')


def get_class_id(cls):
    # http://stackoverflow.com/questions/1175208/elegant-python-function-to-convert-camelcase-to-snake-case
    if cls is None:
        return ''
    name = cls.__name__
    s1 = first_cap_re.sub(r'\1_\2', name)
    return all_cap_re.sub(r'\1_\2', s1).lower()


def get_func(function, extra_annotations=None):
    """
    Given a function which is fully type-annotated,
    returns a `Func` instance, describing the type information.
    """
    inputs = tuple([
        Input(argname, get_class_id(input_type), argname if use_subkey else None)
        for argname, input_type, use_subkey in get_input_types(function, extra_annotations)
    ])
    output = get_class_id(get_output_type(function, extra_annotations))
    return Func(function, inputs, output)



def get_input_types(function, extra_annotations=None):
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

    if extra_annotations:
        annotations = annotations.copy()
        annotations.update(extra_annotations)

    input_types = []
    for argname in argnames:
        input_type = annotations[argname]
        parent_type = getattr(input_type, 'parent_type', None)
        if parent_type is None:
            input_types.append((argname, input_type, False))
        else:
            input_types.append((argname, parent_type, True))
    return input_types


def get_output_type(function, extra_annotations=None):
    if extra_annotations and 'return' in extra_annotations:
        return extra_annotations['return']

    if type(function) == type:
        # Class()
        return function
    elif hasattr(function, '__self__'):
        # @classmethod
        return function.__self__
    # Plain function
    return function.__annotations__['return']


def _build_pipeline(function, initial_types=None, extra_annotations=None):
    pipeline = []
    seen_types = set(initial_types or [])

    # Add all the function's input requirements to the pipeline
    for argname, required_type, use_subkey in get_input_types(function, extra_annotations):
        if required_type in seen_types:
            continue
        this_function = getattr(required_type, 'build')
        this_pipeline, this_seen_types = _build_pipeline(this_function, seen_types)
        pipeline.extend(this_pipeline)
        seen_types |= this_seen_types

    # Add the function itself to the pipeline
    func = get_func(function, extra_annotations)
    output_type = get_output_type(function, extra_annotations)

    pipeline.append(func)
    if output_type is not None:
        seen_types.add(output_type)

    return (pipeline, seen_types)


def build_pipeline(function, initial_types=None, required_type=None, extra_annotations=None):
    """
    Return a Pipeline instance.
    """
    pipeline, seen_types = _build_pipeline(function, initial_types, extra_annotations)
    if (required_type is not None) and (required_type not in seen_types):
        function = getattr(required_type, 'build')
        final_pipeline, seen_types = _build_pipeline(function, seen_types)
        pipeline.extend(final_pipeline)
    return pipeline
