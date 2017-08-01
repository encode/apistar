from apistar.interfaces import Router, StaticFile, StaticFiles, WSGIEnviron
from wsgiref.util import FileWrapper
import apistar
import os
import werkzeug
import whitenoise


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
    def __init__(self, router: Router) -> None:
        package_dir = os.path.dirname(apistar.__file__)
        package_statics = os.path.join(package_dir, 'static')
        self._whitenoise = whitenoise.WhiteNoise(application=None, root=None)
        self._whitenoise.add_files(package_statics, prefix='apistar')
        self._router = router

    def get_file(self, path: str) -> StaticFile:
        if not path.startswith('/'):
            path = '/' + path
        file = self._whitenoise.files.get(path)
        if file is None:
            return None
        return WhiteNoiseStaticFile(file)

    def get_url(self, path: str) -> str:
        return self._router.reverse_url('serve_static', kwargs={'path': path})
