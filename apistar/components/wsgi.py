from apistar.components.base import WSGIEnviron
from apistar.components import http


__all__ = ['WSGIEnviron', 'WSGIResponse']


class WSGIResponse(object):
    __slots__ = ('status', 'headers', 'iterator')

    def __init__(self, status, headers, iterator):
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
