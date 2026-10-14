"""Helper utilities for transaction and ledger domain services."""


def _resolve_tenant_id(tenant_id=None):
    if tenant_id:
        return tenant_id
    from domain.tenant.context import TenantContext
    return TenantContext.optional()
