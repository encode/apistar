from apistar.main import main
from click.testing import CliRunner
from starlette.applications import Starlette
from starlette.responses import JSONResponse
from starlette.testclient import TestClient
import json
import os


def test_valid_document(tmpdir):
    schema = os.path.join(tmpdir, 'schema.json')
    with open(schema, 'w') as schema_file:
        schema_file.write(json.dumps({
            "openapi": "3.0.0",
            "info": {"title": "", "version": ""},
            "paths": {}
        }))

    runner = CliRunner()
    result = runner.invoke(main, ['validate', schema, '--format', 'openapi'])
    assert result.exit_code == 0
    assert result.output == '✓ Valid OpenAPI schema.\n'


def test_invalid_document(tmpdir):
    schema = os.path.join(tmpdir, 'schema.json')
    with open(schema, 'w') as schema_file:
        schema_file.write(json.dumps({
            "openapi": "3.0.0",
            "info": {"version": ""},
        }))

    runner = CliRunner()
    result = runner.invoke(main, ['validate', schema, '--format', 'openapi'])
    assert result.exit_code != 0
    assert result.output == (
        '* The "paths" field is required. (At line 1, column 1.)\n'
        '* The "title" field is required. (At [\'info\'], line 1, column 30.)\n'
        '✘ Invalid OpenAPI schema.\n'
    )


def test_invalid_document_verbose(tmpdir):
    schema = os.path.join(tmpdir, 'schema.json')
    with open(schema, 'w') as schema_file:
        schema_file.write(json.dumps({
            "openapi": "3.0.0",
            "info": {"version": ""},
        }))

    runner = CliRunner()
    result = runner.invoke(main, ['validate', schema, '--format', 'openapi', '--verbose'])
    assert result.exit_code != 0
    assert result.output == (
        '{"openapi": "3.0.0", "info": {"version": ""}}\n'
        '^ The "paths" field is required.\n'
        '                             ^ The "title" field is required.\n'
        '\n'
        '✘ Invalid OpenAPI schema.\n'
    )


def test_docs(tmpdir):
    schema = os.path.join(tmpdir, 'schema.json')
    output_dir = os.path.join(tmpdir, 'build')
    output_index = os.path.join(output_dir, 'index.html')
    with open(schema, 'w') as schema_file:
        schema_file.write(json.dumps({
            "openapi": "3.0.0",
            "info": {"title": "", "version": ""},
            "paths": {}
        }))

    runner = CliRunner()
    result = runner.invoke(main, ['docs', schema, '--format', 'openapi', '--output-dir', output_dir])
    assert result.exit_code == 0
    assert result.output == '✓ Documentation built at "%s".\n' % output_index


app = Starlette()

@app.route('/')
def homepage(request):
    return JSONResponse({'hello': 'world'})


def test_request(tmpdir):
    schema = os.path.join(tmpdir, 'schema.json')
    with open(schema, 'w') as schema_file:
        schema_file.write(json.dumps({
            "openapi": "3.0.0",
            "info": {"title": "", "version": ""},
            "servers": [
                {"url": "https://testserver"}
            ],
            "paths": {
                "/": {
                    "get": {"operationId": "example"}
                }
            }
        }))

    session = TestClient(app)
    runner = CliRunner()
    result = runner.invoke(main, ['request', '--schema', schema, '--format', 'openapi', 'example'], obj=session)
    assert result.exit_code == 0
    assert result.output == '{\n    "hello": "world"\n}\n'


def test_request_verbose(tmpdir):
    schema = os.path.join(tmpdir, 'schema.json')
    with open(schema, 'w') as schema_file:
        schema_file.write(json.dumps({
            "openapi": "3.0.0",
            "info": {"title": "", "version": ""},
            "servers": [
                {"url": "https://testserver"}
            ],
            "paths": {
                "/": {
                    "get": {"operationId": "example"}
                }
            }
        }))

    session = TestClient(app)
    runner = CliRunner()
    result = runner.invoke(main, ['request', '--schema', schema, '--format', 'openapi', '--verbose', 'example'], obj=session)
    assert result.exit_code == 0
    assert '> GET / HTTP/1.1' in result.output
    assert '< 200 OK' in result.output
    assert '{\n    "hello": "world"\n}\n' in result.output
