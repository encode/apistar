class BaseCodec:
    media_type = None

    def decode(self, bytestring, **options):
        raise NotImplementedError()

    def encode(self, item, **options):
        raise NotImplementedError()
