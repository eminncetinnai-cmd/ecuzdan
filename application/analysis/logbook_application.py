"""LogbookApplicationService."""
from application.base import ApplicationService


class LogbookApplicationService(ApplicationService):
    def __init__(self, logbook_service=None, **kwargs):
        super().__init__(**kwargs)
        self.logbook_service = logbook_service

    def list_entries(self, tenant_id, filters=None):
        return self.execute(
            lambda: self.logbook_service.list_entries(tenant_id, filters)
        )

    def create_entry(self, dto, tenant_id, user_id):
        return self.execute(
            lambda: self.logbook_service.create_entry(dto, tenant_id, user_id)
        )

    def detail_payload(self, entry_id, tenant_id):
        return self.execute(
            lambda: self.logbook_service.detail_payload(entry_id, tenant_id)
        )

    def update_entry(self, entry_id, dto, tenant_id):
        return self.execute(
            lambda: self.logbook_service.update_entry(entry_id, dto, tenant_id)
        )

    def delete_entry(self, entry_id, tenant_id):
        return self.execute(
            lambda: self.logbook_service.delete_entry(entry_id, tenant_id)
        )

    def entries_api_payload(self, tenant_id, filters, page=1, per_page=20):
        return self.execute(
            lambda: self.logbook_service.entries_api_payload(
                tenant_id, filters, page, per_page
            )
        )

    def calendar_events(self, tenant_id, filters, color_resolver):
        return self.execute(
            lambda: self.logbook_service.calendar_events(
                tenant_id, filters, color_resolver
            )
        )

    def assets_api_payload(self, tenant_id):
        return self.execute(lambda: self.logbook_service.assets_api_payload(tenant_id))

    def transactions_api_payload(self, tenant_id):
        return self.execute(
            lambda: self.logbook_service.transactions_api_payload(tenant_id)
        )

    def rollback(self):
        if hasattr(self.logbook_service, 'rollback'):
            self.logbook_service.rollback()

