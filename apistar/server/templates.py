import jinja2


class TemplateRenderer():
    def __init__(self, app):
        loader = jinja2.PrefixLoader({
            'apistar': jinja2.PackageLoader('apistar', 'templates')
        })
        self.env = jinja2.Environment(loader=loader)
        self.env.globals['reverse_url'] = app.reverse_url
        self.env.globals['static_url'] = app.static_url

    def render_template(self, path: str, **context):
        template = self.env.get_template(path)
        return template.render(**context)
