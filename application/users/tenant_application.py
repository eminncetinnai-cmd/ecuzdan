"""TenantApplicationService."""
from application.base import ApplicationService


class TenantApplicationService(ApplicationService):
    def __init__(self, tenant_service=None, **kwargs):
        super().__init__(**kwargs)
        self.tenant_service = tenant_service

    def users_context(self, current_user_id):
        return self.execute(lambda: self.tenant_service.users_context(current_user_id))

    def change_user_role(self, current_user_id, target_user_id, new_role):
        return self.execute(
            lambda: self.tenant_service.change_user_role(
                current_user_id, target_user_id, new_role
            )
        )

    def create_invite(self, current_user_id, email, role):
        return self.execute(
            lambda: self.tenant_service.create_invite(current_user_id, email, role)
        )

    def list_invites(self, current_user_id):
        return self.execute(lambda: self.tenant_service.list_invites(current_user_id))

    def rollback(self):
        if hasattr(self.tenant_service, 'rollback'):
            self.tenant_service.rollback()

