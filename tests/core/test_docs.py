import apistar


def test_docs():
    schema = """
    {
        "openapi": "3.0.0",
        "info": {"title": "", "version": ""},
        "paths": {}
    }
    """
    index_html = apistar.docs(schema, format="openapi")
    assert '<title>API Star</title>' in index_html
    assert 'href="/static/css/base.css"' in index_html


def test_docs_with_static_url_func():
    schema = """
    {
        "openapi": "3.0.0",
        "info": {"title": "", "version": ""},
        "paths": {}
    }
    """
    index_html = apistar.docs(schema, format="openapi", static_url=lambda x: '/' + x)
    assert '<title>API Star</title>' in index_html
    assert 'href="/css/base.css"' in index_html
