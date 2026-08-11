"""DashboardApplicationService."""
from application.base import ApplicationService


class DashboardApplicationService(ApplicationService):
    def __init__(self, dashboard_service=None, **kwargs):
        super().__init__(**kwargs)
        self.dashboard_service = dashboard_service

    def index_context(self, tenant_id=None, now=None):
        return self.execute(
            lambda: self.dashboard_service.index_context(tenant_id=tenant_id, now=now)
        )
