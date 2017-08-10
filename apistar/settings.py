from typing import Any, List, Union

from apistar import app
from apistar.core import ArgName


class Settings(dict):
    @classmethod
    def build(cls, app: app.App) -> "Settings":
        return cls(app.settings)

    def get(self, indexes: Union[str, List[str]], default: Any=None) -> Any:
        if isinstance(indexes, str):
            return super().get(indexes, default)

        value = self
        for index in indexes:
            if not isinstance(value, dict):
                return default
            value = value.get(index, default)
        return value


class Setting(object):
    def __new__(cls, *args: Any) -> Any:
        assert len(args) == 1
        return args[0]

    @classmethod
    def build(cls, arg_name: ArgName, settings: Settings) -> "Setting":
        return settings.get(arg_name)
