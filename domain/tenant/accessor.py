"""Accessor helpers for tenant context to be used by code that previously relied on g.get('tenant_id').

This module provides get_tenant and set_tenant convenience functions which maintain backward compatibility.
"""
from .context import TenantContext


def get_tenant(explicit_tenant_id=None):
    """Return the tenant id given an explicit override, falling back to TenantContext.optional()."""
    return explicit_tenant_id or TenantContext.optional()


def set_tenant(tenant_id):
    """Set tenant id in the current context (request or background)."""
    TenantContext.set(tenant_id)
