from io import BytesIO
from itertools import chain

from werkzeug.datastructures import ImmutableMultiDict
from werkzeug.formparser import FormDataParser
from werkzeug.http import parse_options_header

from apistar.codecs.base import BaseCodec


class MultiPartCodec(BaseCodec):
    media_type = 'multipart/form-data'

    def decode(self, bytestring, headers, **options):
        try:
            content_length = max(0, int(headers['content-length']))
        except (KeyError, ValueError, TypeError):
            content_length = None

        try:
            mime_type, mime_options = parse_options_header(headers['content-type'])
        except KeyError:
            mime_type, mime_options = '', {}

        body_file = BytesIO(bytestring)
        parser = FormDataParser()
        stream, form, files = parser.parse(body_file, mime_type, content_length, mime_options)
        return ImmutableMultiDict(chain(form.items(multi=True), files.items(multi=True)))
