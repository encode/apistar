class _ForceMultiPartDict(dict):
    """
    A dictionary that always evaluates as True.
    Allows us to force requests to use multipart encoding, even when no
    file parameters are passed.
    """
    def __bool__(self):
        return True

    def __nonzero__(self):
        return True


class BaseEncoder:
    media_type = None

    def encode(self, options, content):
        raise NotImplementedError()


class JSONEncoder:
    media_type = "application/json"

    def encode(self, options, content):
        options['json'] = content


class URLEncodedEncoder:
    media_type = "application/x-www-form-urlencoded"

    def encode(self, options, content):
        options['data'] = content


class MultiPartEncoder:
    media_type = "multipart/form-data"

    def encode(self, options, content):
        data = {}
        files = _ForceMultiPartDict()

        for key, value in content.items():
            if self.is_file(value):
                files[key] = value
            else:
                data[key] = value
        options['data'] = data
        options['files'] = files

    def is_file(self, item):
        if hasattr(item, '__iter__') and not isinstance(item, (str, list, tuple, dict)):
            # A stream object.
            return True
        return False
