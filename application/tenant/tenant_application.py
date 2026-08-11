"""TenantApplicationService skeleton.

Orchestration for tenant management (invite, activate, suspend, etc.).
"""

from typing import Optional

from application.base import ApplicationService


class TenantApplicationService(ApplicationService):
    def __init__(
        self,
        tenant_service: Optional[object] = None,
        user_service: Optional[object] = None,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.tenant_service = tenant_service
        self.user_service = user_service

    def invite_user(self, tenant_id, payload, **kwargs):
        pass

    def activate_tenant(self, tenant_id, **kwargs):
        pass

    def suspend_tenant(self, tenant_id, **kwargs):
        pass
