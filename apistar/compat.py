# flake8: noqa

try:
    import ujson as json
except ImportError:  # pragma: no cover
    import json  # type: ignore


try:
    import whitenoise
except ImportError:  # pragma: no cover
    whitenoise = None
