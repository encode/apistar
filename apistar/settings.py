from typing import Any, List, Union

from apistar import app
from apistar.core import ArgName, builder


class Settings(dict):

    def get(self, indexes: Union[str, List[str]], default: Any=None) -> Any:
        if isinstance(indexes, str):
            return super().get(indexes, default)

        value = self
        for index in indexes:
            if not isinstance(value, dict):
                return default
            value = value.get(index, default)
        return value


@builder
def build_settings(app: app.App) -> Settings:
    return Settings(app.settings)


class Setting(object):
    def __new__(cls, *args):
        assert len(args) == 1
        return args[0]


@builder
def build_setting(arg_name: ArgName, settings: Settings) -> Setting:
    return settings.get(arg_name)
