from apistar.main import main
from click.testing import CliRunner
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
