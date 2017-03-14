from apistar import pipelines


# Some mock types:

class WSGIRequest(object):
    pass

class Session(object):
    pass

class Response(object):
    pass

class WSGIResponse(object):
    pass


# Some mock functions with a type dependancy chain:

def get_session(req: WSGIRequest) -> Session:
    pass


def finalize_wsgi(req: Response) -> WSGIResponse:
    pass


def view(session: Session, req: WSGIRequest) -> Response:
    pass


def test_get_func():
    """
    Ensure `get_func` can properly resolve a functions annotations,
    and return a `Func` instance.
    """
    func = pipelines.get_func(view)
    assert func.function == view
    print(func.inputs)
    print(type(func.inputs))
    assert func.inputs == (('session', 'session'), ('req', 'wsgi_request'))
    assert func.output == 'response'


# def test_build_pipeline():
#     """
#     Ensure `build_pipeline` can correctly resolve a type dependancy chain
#     for plain functions, and return a corresponding list of `Func` instances.
#     """
#     functions = [get_session, finalize_wsgi, view]
#     required = WSGIResponse
#     initial = [WSGIRequest]
#     pipeline = pipelines.build_pipeline(functions, initial, required)
#     functions = [func.function for func in pipeline]
#     assert functions == [get_session, view, finalize_wsgi]
#
#
# def test_build_cls_pipeline():
#     class Foo:
#         pass
#     class Bar:
#         @classmethod
#         def build(cls, foo: Foo):
#             pass
#     class Baz:
#         @classmethod
#         def build(cls, foo: Foo, bar: Bar):
#             pass
#     def run_me(baz: Baz) -> int:
#         pass
#
#     pipeline, seen = pipelines.build_function_pipeline([run_me], [])
#     functions = [func.function for func in pipeline]
#     assert functions == [Foo, Bar.build, Baz.build, run_me]
