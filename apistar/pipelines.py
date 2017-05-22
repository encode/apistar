import inspect
import re
from collections import namedtuple
from typing import Any, Callable, Dict, List  # noqa

from apistar.util import resolve_class

empty = inspect.Signature.empty
FIRST_CAP_RE = re.compile('(.)([A-Z][a-z]+)')
ALL_CAP_RE = re.compile('([a-z0-9])([A-Z])')


Step = namedtuple('Step', ('function', 'inputs', 'output', 'extra_kwargs'))
Input = namedtuple('Input', ('arg_name', 'state_key'))


class Pipeline(list):
    pass


class ArgName(str):
    """
    A type annotation that may be used in a class `build` method, in order
    to inject the argument name that the annotation is being used with.
    """
    pass


def parameterize_by_argument_name(cls: type) -> bool:
    """
    Return `True` if the class build method includes any `ArgName` markers.
    """
    cls_build = getattr(cls, 'build', None)
    if cls_build is None:
        return False
    signature = inspect.signature(cls_build)
    for parameter in signature.parameters.values():
        if parameter.annotation == ArgName:
            return True
    return False


def get_class_id(cls: type,
                 arg_name: str=None) -> str:
    # http://stackoverflow.com/questions/1175208/elegant-python-function-to-convert-camelcase-to-snake-case
    name = cls.__name__
    s1 = FIRST_CAP_RE.sub(r'\1_\2', name)
    s2 = ALL_CAP_RE.sub(r'\1_\2', s1).lower()
    if parameterize_by_argument_name(cls):
        return '%s:%s' % (s2, arg_name)
    return s2


def run_pipeline(pipeline: Pipeline,
                 state: Dict[str, Any]) -> None:
    for function, inputs, output, extra_kwargs in pipeline:

        kwargs = {}
        for arg_name, state_key in inputs:
            kwargs[arg_name] = state[state_key]
        if extra_kwargs is not None:
            kwargs.update(extra_kwargs)

        state[output] = function(**kwargs)


def _build_step(function: Callable,
                arg_name: str=None,
                extra_annotations: Dict[str, Any]=None) -> Step:
    """
    Given a function, return the single pipeline step that
    corresponds to calling that function.
    """
    extra_annotations = extra_annotations or {}

    signature = inspect.signature(function)
    extra_kwargs = {}

    inputs = []
    for parameter in signature.parameters.values():
        if parameter.name in extra_annotations:
            parameter_cls = extra_annotations[parameter.name]
        else:
            parameter_cls = parameter.annotation

        parameter_cls = resolve_class(parameter_cls)

        if parameter_cls == ArgName:
            extra_kwargs[parameter.name] = arg_name
        else:
            input = (parameter.name, get_class_id(parameter_cls, parameter.name))
            inputs.append(input)

    if 'return' in extra_annotations:
        return_cls = resolve_class(extra_annotations['return'])
    else:
        return_cls = signature.return_annotation
        if return_cls is empty:
            return_cls = getattr(function, '__self__', None)

    output = get_class_id(return_cls, arg_name)

    return Step(function, inputs, output, extra_kwargs)


def _build_pipeline(function: Callable,
                    arg_name: str=None,
                    seen: set=None,
                    extra_annotations: Dict[str, Any]=None) -> Pipeline:
    """
    Given a function, return the pipeline that runs that
    function and all its dependancies.
    """
    pipeline = Pipeline()
    seen = seen or set()
    extra_annotations = extra_annotations or {}

    signature = inspect.signature(function)
    for parameter in signature.parameters.values():
        annotation = extra_annotations.get(parameter.name, parameter.annotation)
        annotation = resolve_class(annotation)
        if get_class_id(annotation, parameter.name) in seen:
            # Don't build a dependancy if it has already been satisfied.
            continue

        if annotation == ArgName:
            continue

        build_function = annotation.build
        dependancy = _build_pipeline(build_function, seen=seen, arg_name=parameter.name)
        pipeline.extend(dependancy)
        seen |= set([step.output for step in dependancy])

    step = _build_step(function, arg_name, extra_annotations)
    pipeline.append(step)
    return pipeline


def build_pipeline(function: Callable,
                   initial_types: List[type]=None,
                   required_type: type=None,
                   extra_annotations: Dict[str, Any]=None) -> Pipeline:
    seen = None
    if initial_types:
        seen = set([get_class_id(cls) for cls in initial_types])
    pipeline = _build_pipeline(function, seen=seen, extra_annotations=extra_annotations)
    if required_type is not None:
        seen |= set([step.output for step in pipeline])
        if get_class_id(required_type) not in seen:
            final_pipeline = _build_pipeline(required_type.build, seen=seen)  # type: ignore
            pipeline.extend(final_pipeline)
    return pipeline
