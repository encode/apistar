from typing import Iterable, List, Tuple

from werkzeug.http import HTTP_STATUS_CODES

from apistar import http

__all__ = ['WSGIEnviron', 'WSGIResponse']


STATUS_CODES = {
    code: "%d %s" % (code, msg)
    for code, msg in HTTP_STATUS_CODES.items()
}


WSGIEnviron = http.WSGIEnviron


class WSGIResponse(object):
    __slots__ = ('status', 'headers', 'iterator')

    def __init__(self, status: str, headers: List[Tuple[str, str]], iterator: Iterable[bytes]):
        self.status = status
        self.headers = headers
        self.iterator = iterator

    @classmethod
    def build(cls, response: http.Response):
        try:
            status_text = STATUS_CODES[response.status]
        except KeyError:
            status_text = str(response.status)

        return WSGIResponse(
            status=status_text,
            headers=list(response.headers.items()),
            iterator=[response.content]
        )
