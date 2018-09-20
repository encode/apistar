import pytest

import apistar
from apistar.schemas import OpenAPI

filenames = [
    'testcases/openapi/api-with-examples.yaml',
    # 'testcases/openapi/callback-example.yaml',
    # 'testcases/openapi/link-example.yaml',
    'testcases/openapi/petstore-expanded.yaml',
    'testcases/openapi/petstore.yaml',
    'testcases/openapi/uspto.yaml',
]


@pytest.mark.parametrize("filename", filenames)
def test_openapi(filename):
    with open(filename, 'rb') as input_file:
        content = input_file.read()

    value = apistar.validate(content, format='openapi')
    OpenAPI().load(value)
