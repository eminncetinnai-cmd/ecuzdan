"""Admin application service."""
import domain.admin.services as admin_domain
from application.base import ApplicationService


class AdminApplicationService(ApplicationService):
    def get_current_user(self, user_id):
        return self.execute(lambda: admin_domain.get_current_user_service(user_id))

    def get_user_or_raise(self, user_id):
        return self.execute(lambda: admin_domain.get_user_or_raise(user_id))

    def get_users_for_admin(self, current_user):
        return self.execute(lambda: admin_domain.get_users_for_admin(current_user))

    def create_user(self, current_user, username, password, role, tenant_id):
        return self.execute(
            lambda: admin_domain.create_user_service(current_user, username, password, role, tenant_id)
        )

    def update_user(self, current_user, user_id, username, password, role, tenant_id):
        return self.execute(
            lambda: admin_domain.update_user_service(current_user, user_id, username, password, role, tenant_id)
        )

    def delete_user(self, current_user, user_id):
        return self.execute(lambda: admin_domain.delete_user_service(current_user, user_id))

    def get_all_tenants(self):
        return self.execute(lambda: admin_domain.get_all_tenants())

    def create_tenant(self, tenant_id, name, created_by=None):
        return self.execute(lambda: admin_domain.create_tenant_service(tenant_id, name, created_by))

    def edit_tenant(self, tenant_id, name, updated_by=None):
        return self.execute(lambda: admin_domain.edit_tenant_service(tenant_id, name, updated_by))

    def update_tenant_status(self, tenant_id, status, updated_by=None):
        return self.execute(
            lambda: admin_domain.update_tenant_status_service(tenant_id, status, updated_by)
        )

    def get_admin_dashboard_stats(self, current_user):
        return self.execute(lambda: admin_domain.get_admin_dashboard_stats(current_user))

    def get_user_stats(self, current_user):
        return self.execute(lambda: admin_domain.get_user_stats(current_user))

