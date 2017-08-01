import os
from importlib.util import find_spec
from wsgiref.util import FileWrapper

import werkzeug
import whitenoise

import apistar
from apistar.interfaces import Router, StaticFile, StaticFiles, WSGIEnviron


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
        return werkzeug.Response(content, status=response.status, headers=list(response.headers))


class WhiteNoiseStaticFiles(StaticFiles):
    static_dir = None
    packages = ['apistar']

    def __init__(self, router: Router) -> None:
        app = whitenoise.WhiteNoise(application=None, root=self.static_dir)
        for package in self.packages:
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
            return self._router.reverse_url('serve_static', kwargs={'path': path})
        except exceptions.NoReverseMatch:
            msg = (
                'The "serve_static" handler must be included in the App routes '
                'in order to use WhiteNoiseStaticFiles'
            )
            raise exceptions.ConfigurationError(msg) from None

    @classmethod
    def configure(cls, **kwargs):
        return type(cls.__name__, (cls,), kwargs)
