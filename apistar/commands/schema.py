from coreapi.utils import get_installed_codecs

from apistar import exceptions
from apistar.interfaces import Schema

codecs = {
    name: codec for name, codec in get_installed_codecs().items()
    if '+' in codec.media_type
}


def schema(schema: Schema,
           format: str='corejson') -> str:
    """
    Generate an API schema.

    Args:
      format:  The format for the API Schema output.

    Returns:
      The API schema.
    """
    try:
        codec = codecs[format]
    except KeyError:
        message = 'Unsupported format: %s\nSupported formats are: %s' % (
                format, ', '.join(codecs.keys()))
        raise exceptions.CommandLineError(message)
    output = codec.encode(schema)
    if isinstance(output, bytes):
        output = output.decode('utf_8')
    return output
