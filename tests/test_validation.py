from apistar import test, types, validators
from apistar.document import Document, Field, Link
from apistar.server.app import App
from apistar.server.core import bind
from apistar.server.validation import ValidatedRequestData


def str_path_param(param: str):
    return {"param": param}


def int_path_param(param: int):
    return {"param": param}


def str_query_param(param: str):
    return {"param": param}


def int_query_param(param: int):
    return {"param": param}


def str_query_param_with_default(param: str = ""):
    return {"param": param}


def int_query_param_with_default(param: int = None):
    return {"param": param}


def schema_enforced_str_path_param(param):
    return {"param": param}


def schema_enforced_int_path_param(param):
    return {"param": param}


def schema_enforced_str_query_param(param):
    return {"param": param}


def schema_enforced_int_query_param(param):
    return {"param": param}


class User(types.Type):
    name = validators.String(max_length=10)
    age = validators.Integer(minimum=0, allow_null=True, default=None)


def type_body_param(user: User):
    return {"user": user}


def schema_enforced_body_param(user: ValidatedRequestData):
    return {"user": user}


document = Document(
    [
        # Path parameters
        Link(url="/str_path_param/{param}/", method="GET", name="str_path_param"),
        Link(url="/int_path_param/{param}/", method="GET", name="int_path_param"),
        Link(
            url="/schema_enforced_str_path_param/{param}/",
            method="GET",
            name="schema_enforced_str_path_param",
            fields=[
                Field(
                    name="param",
                    location="path",
                    required=True,
                    schema=validators.String(max_length=3),
                )
            ],
        ),
        Link(
            url="/schema_enforced_int_path_param/{param}/",
            method="GET",
            name="schema_enforced_int_path_param",
            fields=[
                Field(
                    name="param",
                    location="path",
                    required=True,
                    schema=validators.Integer(minimum=0, maximum=1000),
                )
            ],
        ),
        # Query parameters
        Link(url="/str_query_param/", method="GET", name="str_query_param"),
        Link(url="/int_query_param/", method="GET", name="int_query_param"),
        Link(
            url="/str_query_param_with_default/",
            method="GET",
            name="str_query_param_with_default",
        ),
        Link(
            url="/int_query_param_with_default/",
            method="GET",
            name="int_query_param_with_default",
        ),
        Link(
            url="/schema_enforced_str_query_param/",
            method="GET",
            name="schema_enforced_str_query_param",
            fields=[
                Field(
                    name="param",
                    location="query",
                    schema=validators.String(max_length=3),
                )
            ],
        ),
        Link(
            url="/schema_enforced_int_query_param/",
            method="GET",
            name="schema_enforced_int_query_param",
            fields=[
                Field(
                    name="param",
                    location="query",
                    schema=validators.Integer(minimum=0, maximum=1000),
                )
            ],
        ),
        # Body parameters
        Link(url="/type_body_param/", method="POST", handler=type_body_param),
        Link(
            url="/schema_enforced_body_param/",
            method="POST",
            name="schema_enforced_body_param",
            encoding="application/json",
            fields=[
                Field(
                    name="param",
                    location="body",
                    schema=validators.Object(
                        properties={
                            "name": validators.String(max_length=10),
                            "age": validators.Integer(
                                minimum=0, allow_null=True, default=None
                            ),
                        }
                    ),
                )
            ],
        ),
    ]
)


routes = bind(
    document,
    {
        "str_path_param": str_path_param,
        "int_path_param": int_path_param,
        "schema_enforced_str_path_param": schema_enforced_str_path_param,
        "schema_enforced_int_path_param": schema_enforced_int_path_param,
        "str_query_param": str_query_param,
        "int_query_param": int_query_param,
        "str_query_param_with_default": str_query_param_with_default,
        "int_query_param_with_default": int_query_param_with_default,
        "schema_enforced_str_query_param": schema_enforced_str_query_param,
        "schema_enforced_int_query_param": schema_enforced_int_query_param,
        "type_body_param": type_body_param,
        "schema_enforced_body_param": schema_enforced_body_param,
    },
)

app = App(routes=routes)
client = test.TestClient(app)


def test_str_path_param():
    response = client.get("/str_path_param/123/")
    assert response.json() == {"param": "123"}


def test_schema_enforced_str_path_param():
    response = client.get("/schema_enforced_str_path_param/123/")
    assert response.json() == {"param": "123"}

    response = client.get("/schema_enforced_str_path_param/1234/")
    assert response.status_code == 404
    assert response.json() == {"param": "Must have no more than 3 characters."}


def test_int_path_param():
    response = client.get("/int_path_param/123/")
    assert response.json() == {"param": 123}


def test_schema_enforced_int_path_param():
    response = client.get("/schema_enforced_int_path_param/123/")
    assert response.json() == {"param": 123}

    response = client.get("/schema_enforced_int_path_param/1234/")
    assert response.status_code == 404
    assert response.json() == {"param": "Must be less than or equal to 1000."}


def test_str_query_param():
    response = client.get("/str_query_param/?param=123")
    assert response.json() == {"param": "123"}

    response = client.get("/str_query_param/")
    assert response.json() == {"param": "This field is required."}


def test_str_query_param_with_default():
    response = client.get("/str_query_param_with_default/?param=123")
    assert response.json() == {"param": "123"}

    response = client.get("/str_query_param_with_default/")
    assert response.json() == {"param": ""}


def test_schema_enforced_str_query_param():
    response = client.get("/schema_enforced_str_query_param/?param=123")
    assert response.json() == {"param": "123"}

    response = client.get("/schema_enforced_str_query_param/?param=1234")
    assert response.status_code == 400
    assert response.json() == {"param": "Must have no more than 3 characters."}


def test_int_query_param():
    response = client.get("/int_query_param/?param=123")
    assert response.json() == {"param": 123}

    response = client.get("/int_query_param/")
    assert response.json() == {"param": "This field is required."}


def test_int_query_param_with_default():
    response = client.get("/int_query_param_with_default/?param=123")
    assert response.json() == {"param": 123}

    response = client.get("/int_query_param_with_default/")
    assert response.json() == {"param": None}


def test_schema_enforced_int_query_param():
    response = client.get("/schema_enforced_int_query_param/?param=123")
    assert response.json() == {"param": 123}

    response = client.get("/schema_enforced_int_query_param/?param=1234")
    assert response.status_code == 400
    assert response.json() == {"param": "Must be less than or equal to 1000."}


def test_type_body_param():
    response = client.post("/type_body_param/", json={"name": "tom"})
    assert response.json() == {"user": {"name": "tom", "age": None}}

    response = client.post("/type_body_param/", json={"name": "x" * 100})
    assert response.status_code == 400
    assert response.json() == {"name": "Must have no more than 10 characters."}

    response = client.post("/type_body_param/", json={})
    assert response.status_code == 400
    assert response.json() == {"name": "This field is required."}


def test_schema_enforced_body_param():
    response = client.post("/schema_enforced_body_param/", json={"name": "tom"})
    assert response.json() == {"user": {"name": "tom", "age": None}}

    response = client.post("/schema_enforced_body_param/", json={"name": "x" * 100})
    assert response.status_code == 400
    assert response.json() == {"name": "Must have no more than 10 characters."}
