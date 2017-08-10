# flake8: noqa

try:
    from apistar.backends.django_backend import DjangoBackend
except ImportError:  # pragma: no cover
    DjangoBackend = None  # type: ignore


try:
    from apistar.backends.sqlalchemy_backend import SQLAlchemy
except ImportError:  # pragma: no cover
    SQLAlchemy = None  # type: ignore
