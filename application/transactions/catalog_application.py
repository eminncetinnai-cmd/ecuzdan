from application.base import ApplicationService
from domain.transactions.services import CatalogService


class CatalogApplicationService(ApplicationService):
    """Application layer for catalog operations. Orchestrates calls to domain CatalogService.

    This class intentionally contains no business logic; it forwards calls to the domain service
    and can be extended later to add cross-cutting concerns (transactions, validation, logging).
    It now inherits from ApplicationService so hooks and adapters are available.
    """

    def __init__(self, domain_service: CatalogService = None, **kwargs):
        super().__init__(**kwargs)
        self._svc = domain_service

    def add_from_form(self, form, tenant_id=None, user_id=None):
        return self.execute(lambda: self._svc.add_from_form(form, tenant_id=tenant_id, user_id=user_id))

    def page_context(self, tenant_id=None):
        return self.execute(lambda: self._svc.page_context(tenant_id))

    def update_category(self, id, name, type_, tenant_id=None, code=None, parent_id=None, budget_limit=None, budget_limit_provided=False, version=None, user_id=None, color=None, icon=None):
        return self.execute(lambda: self._svc.update_category(
            id, name, type_, tenant_id=tenant_id, code=code,
            parent_id=parent_id,
            budget_limit=budget_limit, budget_limit_provided=budget_limit_provided,
            version=version, user_id=user_id,
            color=color, icon=icon
        ))

    def restore_category(self, id, tenant_id=None, user_id=None):
        return self.execute(lambda: self._svc.restore_category(id, tenant_id=tenant_id, user_id=user_id))

    def merge_categories(self, source_id, target_id, tenant_id=None, user_id=None):
        return self.execute(lambda: self._svc.merge_categories(source_id, target_id, tenant_id=tenant_id, user_id=user_id))

    def delete_category(self, id, tenant_id=None):
        return self.execute(lambda: self._svc.delete_category(id, tenant_id=tenant_id))

    def update_asset_type(self, id, name):
        return self.execute(lambda: self._svc.update_asset_type(id, name))

    def delete_asset_type(self, id):
        return self.execute(lambda: self._svc.delete_asset_type(id))

    def update_asset_sector(self, id, name):
        return self.execute(lambda: self._svc.update_asset_sector(id, name))

    def delete_asset_sector(self, id):
        return self.execute(lambda: self._svc.delete_asset_sector(id))
