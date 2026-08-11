"""PortfolioApplicationService — Application Layer façade for portfolio endpoints.

No business logic here — routes call use-case methods; domain services implement rules.
All methods are thin pass-throughs with the execute() lifecycle hook.
"""

import logging
from typing import Optional

from application.base import ApplicationService
from domain.portfolio.services import get_yearly_performance

logger = logging.getLogger(__name__)


class PortfolioApplicationService(ApplicationService):
    def __init__(
        self,
        portfolio_service: Optional[object] = None,
        reporting_service: Optional[object] = None,
        tenant_service: Optional[object] = None,
        asset_service: Optional[object] = None,
        outbox=None,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.portfolio_service = portfolio_service
        self.reporting_service = reporting_service
        self.tenant_service = tenant_service
        self.asset_service = asset_service
        self._outbox = outbox

    # ── Placeholder use-cases (future) ────────────────────────────────────────
    def rebalance_portfolio(self, portfolio_id, **kwargs):
        pass

    def optimize(self, portfolio_id, **kwargs):
        pass

    def import_assets(self, data, **kwargs):
        pass

    def export_assets(self, portfolio_id, **kwargs):
        pass

    # ── Asset page contexts (pass-throughs to AssetService) ───────────────────
    def unified_context(self, tenant_id=None):
        """Return context dict for /assets (main portfolio page)."""
        return self.execute(lambda: self.asset_service.unified_context(tenant_id))

    def assets_view_context(self, tenant_id=None):
        """Return context dict for /assets_view."""
        return self.execute(lambda: self.asset_service.assets_view_context(tenant_id))

    def management_context(self, page=1, edit_id=None, tenant_id=None):
        """Return context dict for /assets_management."""
        return self.execute(
            lambda: self.asset_service.management_context(
                page=page, edit_id=edit_id, tenant_id=tenant_id
            )
        )

    # ── Investment performance (pass-through to domain service) ───────────────
    def investment_performance_context(self, tenant_id=None):
        """Return yearly performance dict for /investment_performance."""
        return self.execute(lambda: get_yearly_performance(tenant_id))
