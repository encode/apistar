from apistar.interfaces import Auth


class IsAuthenticated():
    def has_permission(self, auth: Auth):
        return auth.is_authenticated()
