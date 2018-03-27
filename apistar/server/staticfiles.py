from importlib.util import find_spec
import os
import whitenoise

from apistar import exceptions
from apistar.server.wsgi import WSGIEnviron, WSGIStartResponse


class BaseStaticFiles():
    def __call__(self, environ, start_response):
        raise NotImplementedError()


class StaticFiles(BaseStaticFiles):
    def __init__(self, prefix, static_dir=None, static_packages=None):
        self.whitenoise = whitenoise.WhiteNoise(application=self.not_found)
        if static_dir is not None:
            self.whitenoise.add_files(static_dir, prefix=prefix)
        for package in static_packages or []:
            package_dir = os.path.dirname(find_spec(package).origin)
            package_dir = os.path.join(package_dir, 'static')
            package_prefix = prefix.rstrip('/') + '/' + package
            self.whitenoise.add_files(package_dir, prefix=package_prefix)

    def __call__(self, environ, start_response):
        return self.whitenoise(environ, start_response)

    def not_found(self, environ, start_response):
        raise exceptions.NotFound()
