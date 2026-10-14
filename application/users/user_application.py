"""Application facade for user-facing authentication and tenant operations."""

from application.base import ApplicationService


class UserApplicationService(ApplicationService):
    """Coordinate user use-cases across auth, profile, and tenant services.

    The composition root historically referenced this facade, while the concrete
    application services live in separate modules. Keeping the orchestration thin
    preserves the existing layered architecture and gives callers one stable
    application-layer entry point.
    """

    def __init__(
        self,
        auth_service=None,
        profile_service=None,
        tenant_service=None,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.auth_service = auth_service
        self.profile_service = profile_service
        self.tenant_service = tenant_service

    def authenticate(self, username, password):
        return self.execute(
            lambda: self.auth_service.authenticate(username, password)
        )

    def register_user(self, *args, **kwargs):
        return self.execute(
            lambda: self.auth_service.register_user(*args, **kwargs)
        )

    def get_current_user(self, user_id):
        return self.execute(lambda: self.auth_service.get_current_user(user_id))

    def profile_context(self, tenant_id, user_id):
        return self.execute(
            lambda: self.profile_service.index_context(tenant_id, user_id)
        )

    def users_context(self, current_user_id):
        return self.execute(
            lambda: self.tenant_service.users_context(current_user_id)
        )

    def create_invite(self, current_user_id, email, role):
        return self.execute(
            lambda: self.tenant_service.create_invite(
                current_user_id, email, role
            )
        )

    def list_invites(self, current_user_id, tenant_id):
        return self.execute(
            lambda: self.tenant_service.list_invites(current_user_id, tenant_id)
        )
