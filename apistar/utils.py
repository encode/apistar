import os
import sys

from importlib import import_module

from apistar import exceptions, interfaces


def import_object(spec: str):
    parts = spec.split(":", 1)
    module, obj = parts[0], parts[1]

    try:
        sys.path.insert(0, '.')
        if module in sys.modules:
            del sys.modules[module]
        mod = import_module(module)
        del sys.path[0]
    except (ModuleNotFoundError, ValueError, ImportError) as exc:
        if module.endswith(".py") and os.path.exists(module):
            msg_template = "Failed to find application, did you mean '%s:%s'?"
            msg = msg_template % (module.rsplit(".", 1)[0], obj)
            raise exceptions.ConfigurationError(msg)
        else:
            raise exceptions.ConfigurationError() from exc
    try:
        return eval(obj, vars(mod))
    except NameError:
        msg = "Failed to find application object %r in %r" % (obj, module)
        raise exceptions.ConfigurationError(msg)


def import_app(spec: str):
    obj = import_object(spec)
    if not isinstance(obj, interfaces.App):
        msg = "Application object must implement apistar.App"
        raise exceptions.ConfigurationError(msg)
    return obj
