import typing

from apistar.compat import jinja2


class BaseTemplates():
    def render_template(self, path: str, **context):
        raise NotImplementedError()


class Templates(BaseTemplates):
    def __init__(self,
                 template_dir: str=None,
                 packages: typing.Sequence[str]=None,
                 global_context: dict=None):
        if jinja2 is None:
            raise RuntimeError('`jinja2` must be installed to use `Templates`.')

        global_context = global_context if global_context else {}

        loader = jinja2.PrefixLoader({
            package_name: jinja2.PackageLoader(package_name, 'templates')
            for package_name in packages
        })
        if template_dir is not None:
            loader = jinja2.ChoiceLoader([
                jinja2.FileSystemLoader(template_dir),
                loader
            ])

        self.env = jinja2.Environment(autoescape=True, loader=loader)
        for key, value in global_context.items():
            self.env.globals[key] = value

    def render_template(self, path: str, **context):
        template = self.env.get_template(path)
        return template.render(**context)
