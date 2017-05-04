from wsgiref.util import FileWrapper

from apistar import exceptions, schema, wsgi
from apistar.compat import whitenoise
from apistar.settings import Settings


class Statics(object):
    def __init__(self, root_dir):
        assert whitenoise is not None, 'whitenoise must be installed.'
        from whitenoise import WhiteNoise
        self.whitenoise = WhiteNoise(application=None, root=root_dir)

    @classmethod
    def build(cls, settings: Settings):
        root_dir = settings.get(['STATICS', 'ROOT_DIR'])
        return cls(root_dir)


def serve_static(path: schema.Path, statics: Statics, environ: wsgi.WSGIEnviron) -> wsgi.WSGIResponse:
    path = '/' + path.lstrip('/')
    static_file = statics.whitenoise.files.get(path)
    if static_file is None:
        raise exceptions.NotFound()

    response = static_file.get_response(environ['REQUEST_METHOD'], environ)
    status_line = '{} {}'.format(response.status, response.status.phrase)
    headers = list(response.headers)
    if response.file is not None:
        file_wrapper = environ.get('wsgi.file_wrapper', FileWrapper)
        content = file_wrapper(response.file)
    else:
        content = []
    return wsgi.WSGIResponse(status_line, headers, content)
