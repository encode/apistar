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
    import pygments
    from pygments.lexers import get_lexer_by_name
    from pygments.formatters import HtmlFormatter

    def pygments_highlight(text, lang, style):
        lexer = get_lexer_by_name(lang, stripall=False)
        formatter = HtmlFormatter(nowrap=True, style=style)
        return pygments.highlight(text, lexer, formatter)

    def pygments_css(style):
        formatter = HtmlFormatter(style=style)
        return formatter.get_style_defs('.highlight')

except ImportError:
    pygments = None

    def pygments_highlight(text, lang, style):
        return text

    def pygments_css(style):
        return None


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
