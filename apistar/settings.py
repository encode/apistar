from apistar import app
from apistar.pipelines import ArgName


class Settings(dict):
    @classmethod
    def build(cls,
              app: app.App):
        return cls(app.settings)

    def get(self,
            indexes,
            default=None):
        if isinstance(indexes, str):
            return super().get(indexes, default)

        value = self
        for index in indexes:
            if not isinstance(value, dict):
                return default
            value = value.get(index, default)
        return value


class Setting(object):
    def __new__(cls, *args):
        assert len(args) == 1
        return args[0]

    @classmethod
    def build(cls,
              arg_name: ArgName,
              settings: Settings):
        return settings.get(arg_name)
