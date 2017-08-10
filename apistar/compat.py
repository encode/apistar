# flake8: noqa

try:
    import ujson as json
except ImportError:  # pragma: no cover
    import json  # type: ignore


try:
    import whitenoise
except ImportError:  # pragma: no cover
    whitenoise = None


# requests >=2.16.0 no longer includes vendored packages and lists urllib3 as a dependency
try:
    import urllib3
except ImportError:  # pragma: no cover
    # requests installation is <2.16.0
    import requests
    urllib3 = requests.packages.urllib3
