import os
from wsgiref.util import FileWrapper

import apistar
from apistar import exceptions, wsgi
from apistar.compat import whitenoise
from apistar.decorators import exclude_from_schema
from apistar.routing import Path
from apistar.settings import Settings

PACKAGE_DIR = os.path.dirname(apistar.__file__)
PACKAGE_STATICS = os.path.join(PACKAGE_DIR, 'static')


class Statics(object):
    preload = True

    def __init__(self, root_dir=None):
        assert whitenoise is not None, 'whitenoise must be installed.'
        from whitenoise import WhiteNoise
        self.whitenoise = WhiteNoise(application=None, root=root_dir)
        self.whitenoise.add_files(PACKAGE_STATICS, prefix='apistar')

    @classmethod
    def build(cls, settings: Settings):
        root_dir = settings.get(['STATICS', 'DIR'])
        return cls(root_dir)


@exclude_from_schema
def serve_static(path: Path, statics: Statics, environ: wsgi.WSGIEnviron) -> wsgi.WSGIResponse:
    if not path.startswith('/'):
        path = Path('/' + path)
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
        # We hit this branch for HEAD requests
        content = []
    return wsgi.WSGIResponse(status_line, headers, content)
