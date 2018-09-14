import pytest
from apistar.schemas import Swagger
from apistar.validate import validate


filenames = [
    'testcases/swagger/api-with-examples.yaml',
    'testcases/swagger/petstore-expanded.yaml',
    'testcases/swagger/petstore-minimal.yaml',
    'testcases/swagger/petstore-simple.yaml',
    'testcases/swagger/petstore-with-external-docs.yaml',
    'testcases/swagger/petstore.yaml',
    'testcases/swagger/uber.yaml',
    'testcases/swagger/swagger.json',
]


@pytest.mark.parametrize("filename", filenames)
def test_openapi(filename):
    with open(filename, 'rb') as input_file:
        content = input_file.read()

    value = validate(content, format='swagger')
    Swagger().load(value)