import os
from typing import List  # noqa

import jinja2

from apistar.core import ArgName
from apistar.exceptions import ConfigurationError
from apistar.settings import Settings


class Templates(jinja2.Environment):
    preload = True

    @classmethod
    def build(cls, settings: Settings) -> "Templates":
        template_dirs = settings.get(['TEMPLATES', 'DIRS'])

        package_loaders = [
            jinja2.PrefixLoader({
                'apistar': jinja2.PackageLoader('apistar', 'templates')
            })
        ]  # type: List[jinja2.BaseLoader]

        if template_dirs is None:
            filesystem_loaders = []  # type: List[jinja2.BaseLoader]
        else:
            filesystem_loaders = [
                jinja2.FileSystemLoader(template_dir)
                for template_dir in template_dirs
            ]

        loader = jinja2.ChoiceLoader(package_loaders + filesystem_loaders)
        return Templates(loader=loader)


class Template(jinja2.Template):
    prefix = ''
    suffixes = ['.html', '.txt']
    path_delimiter = '__'

    @classmethod
    def build(cls, arg_name: ArgName, templates: Templates) -> jinja2.Template:
        paths = arg_name.split(cls.path_delimiter)
        path = os.path.join(cls.prefix, *paths)
        for suffix in cls.suffixes:
            try:
                return templates.get_template(path + suffix)
            except jinja2.TemplateNotFound:
                pass
        raise ConfigurationError('No template found for "%s".' % arg_name)
