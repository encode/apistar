from apistar.interfaces import Router, StaticFiles, Template, Templates
import jinja2


class Jinja2Template(Template):
    def __init__(self, template: jinja2.Template) -> None:
        self._template = template

    def render(self, **context) -> str:
        return self._template.render(**context)


class Jinja2Templates(Templates):
    def __init__(self, router: Router, statics: StaticFiles) -> None:
        package_loaders = [
            jinja2.PrefixLoader({
                'apistar': jinja2.PackageLoader('apistar', 'templates')
            })
        ]
        loader = jinja2.ChoiceLoader(package_loaders)
        env = jinja2.Environment(loader=loader)
        env.globals['reverse_url'] = router.reverse_url
        env.globals['static'] = statics.get_url
        self._env = env

    def get_template(self, path: str) -> Template:
        template = self._env.get_template(path)
        if template is None:
            return None
        return Jinja2Template(template)
