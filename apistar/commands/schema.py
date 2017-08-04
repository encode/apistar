from coreapi.utils import get_installed_codecs

from apistar.interfaces import Schema

codecs = {
    name: codec for name, codec in get_installed_codecs().items()
    if '+' in codec.media_type
}


def schema(schema: Schema,
           format: str='corejson') -> None:
    codec = codecs[format]
    return codec.encode(schema)
