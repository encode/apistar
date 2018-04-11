import os

from collections import namedtuple
from http import cookiejar
from typing import Any

File = namedtuple('File', 'name content content_type')
File.__new__.__defaults__ = (None,)


def is_stream_object(obj: Any) -> bool:
    return hasattr(obj, '__iter__') and not isinstance(obj, (str, list, tuple, dict))


def is_file(obj: Any) -> bool:
    if isinstance(obj, File):
        return True

    return is_stream_object(obj)


def guess_filename(obj):
    name = getattr(obj, 'name', None)
    if name and isinstance(name, str) and name[0] != '<' and name[-1] != '>':
        return os.path.basename(name)
    return None


class ForceMultiPartDict(dict):
    """
    A dictionary that always evaluates as True.
    Allows us to force requests to use multipart encoding, even when no
    file parameters are passed.
    """
    def __bool__(self):
        return True

    def __nonzero__(self):
        return True


class BlockAllCookies(cookiejar.CookiePolicy):
    """
    A cookie policy that rejects all cookies.
    Used to override the default `requests` behavior.
    """
    return_ok = set_ok = domain_return_ok = path_return_ok = lambda self, *args, **kwargs: False
    netscape = True
    rfc2965 = hide_cookie2 = False
