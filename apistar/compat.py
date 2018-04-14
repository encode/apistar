import collections
import sys

if sys.version_info < (3, 6):
    dict_type = collections.OrderedDict
else:
    dict_type = dict


try:
    import aiofiles
except ImportError:
    aiofiles = None


try:
    import jinja2
except ImportError:
    jinja2 = None


try:
    import whitenoise
except ImportError:
    whitenoise = None


try:
    # Ideally we subclass `_TemporaryFileWrapper` to present a clear __repr__
    # for downloaded files.
    from tempfile import _TemporaryFileWrapper

    class DownloadedFile(_TemporaryFileWrapper):
        basename = None

        def __repr__(self):
            state = "closed" if self.closed else "open"
            mode = "" if self.closed else " '%s'" % self.file.mode
            return "<DownloadedFile '%s', %s%s>" % (self.name, state, mode)

        def __str__(self):
            return self.__repr__()

except ImportError:
    # On some platforms (eg GAE) the private _TemporaryFileWrapper may not be
    # available, just use the standard `NamedTemporaryFile` function
    # in this case.
    import tempfile

    DownloadedFile = tempfile.NamedTemporaryFile
