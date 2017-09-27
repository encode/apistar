import json
import typing

from werkzeug.datastructures import ImmutableMultiDict
from werkzeug.formparser import FormDataParser
from werkzeug.http import parse_options_header
from werkzeug.urls import url_decode

from apistar import exceptions, http


class JSONParser():
    media_type = 'application/json'

    def parse(self, body: http.Body) -> typing.Any:
        if not body:
            raise exceptions.BadRequest(detail='Empty JSON')
        try:
            return json.loads(body.decode('utf-8'))
        except json.JSONDecodeError:
            raise exceptions.BadRequest(detail='Invalid JSON')


class URLEncodedParser():
    media_type = 'application/x-www-form-urlencoded'

    def parse(self, body: http.Body) -> ImmutableMultiDict:
        return url_decode(body, cls=ImmutableMultiDict)


class MultiPartParser():
    media_type = 'multipart/form-data'

    def get_content_length(self, headers: http.Headers) -> typing.Optional[int]:
        content_length = headers.get('Content-Length')
        if content_length is not None:
            try:
                return max(0, int(content_length))
            except (ValueError, TypeError):
                pass
        return None

    def get_mimetype_and_options(self, headers: http.Headers) -> typing.Tuple[str, dict]:
        content_type = headers.get('Content-Type')
        if content_type:
            return parse_options_header(content_type)
        return '', {}

    def parse(self, headers: http.Headers, stream: http.RequestStream) -> ImmutableMultiDict:
        mimetype, options = self.get_mimetype_and_options(headers)
        content_length = self.get_content_length(headers)
        parser = FormDataParser()
        stream, form, files = parser.parse(stream, mimetype, content_length, options)
        return ImmutableMultiDict(list(form.items()) + list(files.items()))


DEFAULT_PARSERS = [
    JSONParser(),
    URLEncodedParser(),
    MultiPartParser()
]
