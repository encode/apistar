from werkzeug.datastructures import ImmutableMultiDict
from werkzeug.urls import url_decode

from apistar.codecs.base import BaseCodec


class URLEncodedCodec(BaseCodec):
    media_type = 'application/x-www-form-urlencoded'

    def decode(self, bytestring, **options):
        return url_decode(bytestring, cls=ImmutableMultiDict)
