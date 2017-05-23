import pytest

from apistar import App, Route
from apistar.app import builder, get_builder
from apistar.exceptions import APIException, InternalError
from apistar.test import TestClient


def handled_exception():
    raise APIException(detail='error', status_code=400)


def unhandled_exception():
    raise Exception('Oh noes!')


app = App(routes=[
    Route('/handled_exception/', 'GET', handled_exception),
    Route('/unhandled_exception/', 'GET', unhandled_exception),
])


client = TestClient(app)


def test_handled_exception():
    response = client.get('/handled_exception/')
    assert response.status_code == 400
    assert response.json() == {
        'message': 'error'
    }


def test_unhandled_exception():
    with pytest.raises(Exception):
        client.get('/unhandled_exception/')


def test_get_classmethod_builder():
    """ Can define build() as a classmethod
    """

    class A:
        @classmethod
        def build(cls):  # pragma: no cover
            pass
    assert callable(get_builder(A))


def test_get_decorated_builder():
    """ Can define a builder as a decorator
    """

    class B:
        pass

    @builder
    def build_b() -> B:  # pragma: no cover
        pass

    assert callable(get_builder(B))


def test_no_builder_exception():
    """ Complain if a class is put through the build pipeline without a builder
    """

    class C(object):
        pass

    with pytest.raises(InternalError):
        get_builder(C)


def test_multiple_builder_exception():
    """ Complain if more than one builder is assigned to a class
    """

    class D(object):
        @classmethod
        def build(cls):  # pragma: no cover
            pass

    with pytest.raises(InternalError):
        @builder
        def build_d_again() -> D:  # pragma: no cover
            pass


def test_multiple_builder_exception_2():
    """ Complain if more than one builder is assigned to a class
    """

    class E(object):
        pass

    @builder
    def build_e() -> E:  # pragma: no cover
        pass

    with pytest.raises(InternalError):
        @builder
        def build_e_again() -> E:  # pragma: no cover
            pass


def test_unhandled_exception_as_500():
    client = TestClient(app, raise_500_exc=False)
    response = client.get('/unhandled_exception/')
    assert response.status_code == 500
    assert 'Traceback' in response.text
