"""Tenant resolver utilities for domain context.

Framework-agnostic resolver that reads from active domain context.
"""

from __future__ import annotations

from domain.tenant.context import TenantContext


def resolve_from_request() -> str | None:
    """Resolve tenant id from current domain context."""
    return TenantContext.optional()
