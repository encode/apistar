from apistar import app
from apistar.pipelines import ArgName


class Settings(dict):
    @classmethod
    def build(cls, app: app.App):
        return cls(app.settings)


class Setting(object):
    def __new__(cls, *args):
        assert len(args) == 1
        return args[0]

    @classmethod
    def build(cls, arg_name: ArgName, settings: Settings):
        return settings.get(arg_name)
