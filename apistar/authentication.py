from apistar.interfaces import Auth


class Unauthenticated(Auth):
    def is_authenticated(self) -> bool:
        return False

    def get_display_name(self) -> None:
        return None

    def get_user_id(self) -> None:
        return None


class Authenticated(Auth):
    def __init__(self, username, user=None, token=None):
        self.username = username
        self.user = user
        self.token = token

    def is_authenticated(self) -> bool:
        return True

    def get_display_name(self) -> str:
        return self.username

    def get_user_id(self) -> str:
        return self.username
