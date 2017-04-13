import os

from jinja2 import Environment, FileSystemLoader

from apistar.app import AppRoot


class Templates(Environment):
    @classmethod
    def build(cls, app_root: AppRoot):
        template_dir = os.path.join(app_root, 'templates')
        return Templates(
            loader=FileSystemLoader(template_dir)
        )
