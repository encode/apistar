from coreapi.utils import get_installed_codecs

from apistar.interfaces import Schema

codecs = {
    name: codec for name, codec in get_installed_codecs().items()
    if '+' in codec.media_type
}


def schema(schema: Schema,
           format: str='corejson') -> bytes:
    """
    Generate an API schema.

    Args:
      format:  The format for the API Schema output.
    """
    codec = codecs[format]
    return codec.encode(schema)
