from jinja2 import Environment, FileSystemLoader

from apistar.settings import Settings


class Templates(Environment):
    @classmethod
    def build(cls, settings: Settings):
        template_dir = settings['TEMPLATES']['TEMPLATE_DIR']
        return Templates(
            loader=FileSystemLoader(template_dir)
        )
