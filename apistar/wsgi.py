from apistar import http
from typing import Iterable, Tuple, List
from werkzeug.datastructures import ImmutableDict


__all__ = ['WSGIEnviron', 'WSGIResponse']


WSGIEnviron = http.WSGIEnviron


class WSGIResponse(object):
    __slots__ = ('status', 'headers', 'iterator')

    def __init__(self, status: str, headers: List[Tuple[str, str]], iterator: Iterable[bytes]) -> None:
        self.status = status
        self.headers = headers
        self.iterator = iterator

    @classmethod
    def build(cls, response: http.Response):
        return WSGIResponse(
            status={
                200: '200 OK',
                404: '404 NOT FOUND'
            }[response.status],
            headers=list(response.headers.items()),
            iterator=[response.content]
        )
