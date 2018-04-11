import collections
import json

from apistar.codecs.base import BaseCodec
from apistar.exceptions import ParseError


class JSONCodec(BaseCodec):
    media_type = 'application/json'
    format = 'json'

    def decode(self, bytestring, **options):
        """
        Return raw JSON data.
        """
        try:
            return json.loads(
                bytestring.decode('utf-8'),
                object_pairs_hook=collections.OrderedDict
            )
        except ValueError as exc:
            raise ParseError('Malformed JSON. %s' % exc) from None
