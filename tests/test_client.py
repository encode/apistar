import os

import pytest

from apistar import (
    App,
    Client,
    Document,
    Field,
    Include,
    Link,
    Route,
    Section,
    TestClient,
    exceptions,
    http
)


def no_parameter():
    return http.JSONResponse({"hello": "world"})


def query_parameter(params: http.QueryParams):
    return http.JSONResponse({"params": dict(params)})


def body_parameter(data: http.RequestData):
    return http.JSONResponse({"data": data})


def text_response():
    return http.HTMLResponse("Hello, world!")


def empty_response():
    return http.Response(content=b"", status_code=204)


def error_response():
    return http.JSONResponse({"error": "failed"}, status_code=400)


def download_response():
    return http.Response(
        b"...",
        headers={
            "Content-Type": "image/jpeg",
            "Content-Disposition": "attachment; filename=example.jpg;",
        },
    )


def download_response_filename_in_url():
    return http.Response(b"...", headers={"Content-Type": "image/jpeg"})


routes = [
    Include(
        url="/parameters",
        name="parameters",
        routes=[
            Route(url="/no-parameters/", method="GET", handler=no_parameter),
            Route(url="/query-parameter/", method="GET", handler=query_parameter),
            Route(url="/body-parameter/", method="POST", handler=body_parameter),
        ],
    ),
    Include(
        url="/responses",
        name="responses",
        routes=[
            Route(url="/text-response/", method="GET", handler=text_response),
            Route(url="/empty-response/", method="GET", handler=empty_response),
            Route(url="/error-response/", method="GET", handler=error_response),
        ],
    ),
    Include(
        url="/downloads",
        name="downloads",
        routes=[
            Route(url="/download-response/", method="GET", handler=download_response),
            Route(
                url="/download-response/path.jpg",
                method="GET",
                handler=download_response_filename_in_url,
            ),
        ],
    ),
]
app = App(routes=routes)


document = Document(
    url="http://testserver",
    content=[
        Section(
            name="parameters",
            content=[
                Link(
                    name="no_parameter", url="/parameters/no-parameters/", method="GET"
                ),
                Link(
                    name="query_parameter",
                    url="/parameters/query-parameter/",
                    method="GET",
                    fields=[Field(name="a", location="query")],
                ),
                Link(
                    name="body_parameter",
                    url="/parameters/body-parameter/",
                    method="POST",
                    encoding="application/json",
                    fields=[Field(name="a", location="body")],
                ),
            ],
        ),
        Section(
            name="responses",
            content=[
                Link(
                    name="text_response", url="/responses/text-response/", method="GET"
                ),
                Link(
                    name="empty_response",
                    url="/responses/empty-response/",
                    method="GET",
                ),
                Link(
                    name="error_response",
                    url="/responses/error-response/",
                    method="GET",
                ),
            ],
        ),
        Section(
            name="downloads",
            content=[
                Link(
                    name="download_response",
                    url="/downloads/download-response/",
                    method="GET",
                ),
                Link(
                    name="download_response_filename_in_url",
                    url="/downloads/download-response/path.jpg",
                    method="GET",
                ),
            ],
        ),
    ],
)
session = TestClient(app)
client = Client(document=document, session=session)


def test_no_parameters():
    assert client.request("parameters:no_parameter") == {"hello": "world"}


def test_query_parameter():
    assert client.request("parameters:query_parameter", a=1) == {"params": {"a": "1"}}


def test_body_parameter():
    assert (
        client.request("parameters:body_parameter", a={"abc": 123})
        == {"data": {"abc": 123}}
    )


def test_text_response():
    assert client.request("responses:text_response") == "Hello, world!"


def test_empty_response():
    assert client.request("responses:empty_response") is None


def test_error_response():
    with pytest.raises(exceptions.ErrorResponse) as exc:
        client.request("responses:error_response")
    assert exc.value.title == "400 Bad Request"
    assert exc.value.content == {"error": "failed"}


def test_download_response():
    downloaded = client.request("downloads:download_response")
    assert downloaded.read() == b"..."
    assert os.path.basename(downloaded.name) == "example.jpg"


def test_download_response_filename_in_url():
    downloaded = client.request("downloads:download_response_filename_in_url")
    assert downloaded.read() == b"..."
    assert os.path.basename(downloaded.name) == "path.jpg"
