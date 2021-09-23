import os
import pytest

import apistar

filenames = [
    "testcases/openapi/api-with-examples.yaml",
    # 'testcases/openapi/callback-example.yaml',
    # 'testcases/openapi/link-example.yaml',
    "testcases/openapi/petstore-expanded.yaml",
    "testcases/openapi/petstore.yaml",
    "testcases/openapi/uspto.yaml",
]


@pytest.mark.parametrize("filename", filenames)
def test_openapi(filename):
    with open(filename, "rb") as input_file:
        content = input_file.read()

    path, extension = os.path.splitext(filename)
    encoding = {".json": "json", ".yaml": "yaml"}[extension]
    document = apistar.validate(content, format="openapi", encoding=encoding)
    if document.url is not None:
        for link_info in document.walk_links():
            assert document.url in link_info.link.url
