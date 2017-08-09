import os
from importlib.util import find_spec
from wsgiref.util import FileWrapper

import whitenoise

from apistar import exceptions, http
from apistar.interfaces import (
    Router, Settings, StaticFile, StaticFiles, WSGIEnviron
)


class WhiteNoiseStaticFile(StaticFile):
    def __init__(self, whitenoise_file) -> None:
        self._file = whitenoise_file

    def get_response(self, environ: WSGIEnviron):
        method = environ['REQUEST_METHOD']
        response = self._file.get_response(method, environ)
        if response.file is not None:
            file_wrapper = environ.get('wsgi.file_wrapper', FileWrapper)
            content = file_wrapper(response.file)
        else:
            # We hit this branch for HEAD requests
            content = []

        headers = dict(response.headers)
        content_type = headers.pop('Content-Type')
        return http.Response(content, status=response.status, headers=headers, content_type=content_type)


class WhiteNoiseStaticFiles(StaticFiles):
    DEFAULT_SETTINGS = {
        'ROOT_DIR': None,
        'PACKAGE_DIRS': ['apistar']
    }

    def __init__(self, router: Router, settings: Settings) -> None:
        settings = settings.get('STATICS', self.DEFAULT_SETTINGS)
        app = whitenoise.WhiteNoise(application=None, root=settings['ROOT_DIR'])
        for package in settings['PACKAGE_DIRS']:
            package_dir = os.path.dirname(find_spec(package).origin)
            package_statics = os.path.join(package_dir, 'static')
            app.add_files(package_statics, prefix=package)

        self._whitenoise = app
        self._router = router

    def get_file(self, path: str) -> StaticFile:
        if not path.startswith('/'):
            path = '/' + path
        file = self._whitenoise.files.get(path)
        if file is None:
            return None
        return WhiteNoiseStaticFile(file)

    def get_url(self, path: str) -> str:
        try:
            return self._router.reverse_url('serve_static', values={'path': path})
        except exceptions.NoReverseMatch:
            msg = (
                'The "serve_static" handler must be included in the App routes '
                'in order to use WhiteNoiseStaticFiles'
            )
            raise exceptions.ConfigurationError(msg) from None
