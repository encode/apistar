from apistar import exceptions


def negotiate_content_type(codecs, content_type=None):
    """
    Given the value of a 'Content-Type' header, return the appropriate
    codec for decoding the request content.
    """
    if content_type is None:
        return codecs[0]

    content_type = content_type.split(';')[0].strip().lower()
    main_type = content_type.split('/')[0] + '/*'
    wildcard_type = '*/*'

    for codec in codecs:
        if codec.media_type in (content_type, main_type, wildcard_type):
            return codec

    msg = "Unsupported media in Content-Type header '%s'" % content_type
    raise exceptions.NoCodecAvailable(msg)
