from apistar import app


class Settings(dict):
    @classmethod
    def build(cls, app: app.App):
        return cls(app.settings)
