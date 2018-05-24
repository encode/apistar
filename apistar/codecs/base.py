from typing import Optional


class BaseCodec:
    media_type: Optional[str] = None

    def decode(self, bytestring, **options):
        raise NotImplementedError()

    def encode(self, item, **options):
        raise NotImplementedError()
