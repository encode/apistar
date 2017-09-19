import json
import re
import typing

from werkzeug.http import parse_accept_header

from apistar import http

subtype = re.compile('/[^/]*$')


class Renderer():
    media_type = 'text/plain'
    charset = 'utf-8'  # type: typing.Optional[str]

    def render(self, data: http.ResponseData) -> bytes:
        pass

    def get_content_type(self) -> str:
        if self.charset is None:
            return self.media_type
        return '%s; charset=%s' % (self.media_type, self.charset)


class JSONRenderer(Renderer):
    media_type = 'application/json'
    charset = None

    def render(self, data: http.ResponseData) -> bytes:
        return json.dumps(data).encode('utf-8')


class HTMLRenderer(Renderer):
    media_type = 'text/html'
    charset = 'utf-8'

    def render(self, data: http.ResponseData) -> bytes:
        assert isinstance(data, (str, bytes))
        if isinstance(data, str):
            return data.encode(self.charset)
        return typing.cast(bytes, data)


def negotiate_renderer(accept: typing.Optional[str],
                       renderers: typing.List[Renderer]) -> typing.Optional[Renderer]:
    if accept is None:
        return renderers[0]

    for media_type, quality in parse_accept_header(accept):
        if media_type == '*/*':
            return renderers[0]
        elif media_type.endswith('/*'):
            for renderer in renderers:
                match = re.sub(subtype, '/*', renderer.media_type)
                if media_type == match:
                    return renderer
        else:
            for renderer in renderers:
                if media_type == renderer.media_type:
                    return renderer
    return None


DEFAULT_RENDERERS = [
    JSONRenderer()
]
