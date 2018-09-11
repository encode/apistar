class BaseCodec:
    media_type = None
    format = None

    def decode(self, bytestring, **options):
        raise NotImplementedError()
