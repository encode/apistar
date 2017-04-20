import os

import jinja2

from apistar.pipelines import ArgName
from apistar.settings import Settings


class Templates(jinja2.Environment):
    @classmethod
    def build(cls, settings: Settings):
        template_dir = settings['TEMPLATES']['TEMPLATE_DIR']
        return Templates(
            loader=jinja2.FileSystemLoader(template_dir)
        )


class Template(jinja2.Template):
    suffix = '.html'
    path_delimiter = '__'

    @classmethod
    def build(cls, arg_name: ArgName, templates: Templates):
        paths = arg_name.split(cls.path_delimiter)
        path = os.path.join(*paths) + cls.suffix
        return templates.get_template(path)
