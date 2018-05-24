
#
# Test extra codecs
#
import collections
import json
import typing

import pytest

from apistar import App, ASyncApp, Route, http, test
from apistar.codecs import BaseCodec
from apistar.exceptions import ParseError
from apistar.http import Response


class JsonTrollCodec(BaseCodec):
    # Overrides json
    media_type = "application/json"
    format = "json"

    def decode(self, bytestring, **options):
        """
        Return raw JSON data.
        """
        try:
            original = json.loads(
                bytestring.decode("utf-8"), object_pairs_hook=collections.OrderedDict
            )
            original.update({"Not": "Belonging"})
            return original
        except ValueError as exc:
            raise ParseError("Malformed JSON. %s" % exc) from None


class DumbResponse(Response):
    media_type = "text/plain"

    def render(self, content: typing.Any):
        return f"This has been reversed: {content}".encode()


class DumbCodec(BaseCodec):
    media_type = "text/plain"
    response_class = DumbResponse

    def decode(self, bytestring, **options):
        """
        Return disordered data.
        """
        return bytes(sorted(bytestring))


def post_overriden_json(data: http.RequestData):
    return data


def post_disorder(data: http.RequestData):
    return data.decode("UTF-8")


routes = [
    Route("/overriden", method="POST", handler=post_overriden_json),
    Route("/disordered", method="POST", handler=post_disorder),
]


@pytest.fixture(scope="module", params=["wsgi", "asgi"])
def client(request):
    if request.param == "asgi":
        app = ASyncApp(routes=routes, codecs=[JsonTrollCodec(), DumbCodec()])
    else:
        app = App(routes=routes, codecs=[JsonTrollCodec(), DumbCodec()])
    return test.TestClient(app)


def test_overriden_json_codec(client):
    response = client.post("/overriden", json={"Do": "Belong"})
    assert {"Do": "Belong", "Not": "Belonging"} == response.json()


def test_dumb_codec(client):
    response = client.post(
        "/disordered", data="doidhf", headers={"Content-Type": "text/plain"}
    )
    assert response.content == b"This has been reversed: ddfhio"
