from apistar.interfaces import Auth


class IsAuthorized():
    def has_permission(self, auth: Auth):
        return auth.is_authenticated()
