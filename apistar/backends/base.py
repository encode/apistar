from typing import Any, List  # NOQA


class BaseDatabaseBackend(object):
    preload_key = ''
    commands = []  # type: List[Any]
