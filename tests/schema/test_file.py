import io

import pytest

from apistar import app, routing, schema, test, http, exceptions


class File(schema.Object):
    properties = {
        'file': schema.File(max_length=15)
    }


def get_data(data: File) -> http.Response:
    body = data['file'].read().decode('utf-8')
    return http.Response({'body': body})


app = app.App(routes=[
    routing.Route('/upload/', 'POST', get_data),
])

client = test.TestClient(app)


def test_read_data():
    data = 'some buffer'
    response = client.post('http://example.com/upload/', files={'file': io.StringIO(data)})
    assert response.status_code == 200
    assert response.json() == {'body': 'some buffer'}


def test_not_file():
    response = client.post('http://example.com/upload/', data={'file': 'some buffer'})
    assert response.status_code == 400
    assert response.json() == {'file': 'Must be a valid file.'}


def test_empty_file():
    response = client.post('http://example.com/upload/', files={'file': io.StringIO()})
    assert response.status_code == 400
    assert response.json() == {'file': 'The submitted file is empty.'}


def test_max_length():
    response = client.post('http://example.com/upload/', files={'file': io.StringIO('some big buffer!!!')})
    assert response.status_code == 400
    assert response.json() == {'file': 'Ensure this filename has at most 15 characters (it has 18).'}


def test_get_file_size():
    with pytest.raises(exceptions.SchemaError) as exc:
        schema.File.get_file_size('test')
    assert str(exc.value) == "Unable to determine the file's size."
    assert schema.File.get_file_size(io.StringIO('some buffer')) == 11
