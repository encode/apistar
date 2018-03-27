import jinja2


class BaseTemplates():
    def render_template(self, path: str, **context):
        raise NotImplementedError()


class Templates(BaseTemplates):
    def __init__(self,
                 template_dir: str=None,
                 template_packages: list=None,
                 global_context: dict=None):
        template_packages = template_packages if template_packages else []
        global_context = global_context if global_context else {}

        loader = jinja2.PrefixLoader({
            package_name: jinja2.PackageLoader(package_name, 'templates')
            for package_name in template_packages
        })
        if template_dir is not None:
            loader = loader.ChoiceLoader([
                loader.FileSystemLoader(template_dir),
                loader
            ])

        self.env = jinja2.Environment(loader=loader)
        for key, value in global_context.items():
            self.env.globals[key] = value

    def render_template(self, path: str, **context):
        template = self.env.get_template(path)
        return template.render(**context)
