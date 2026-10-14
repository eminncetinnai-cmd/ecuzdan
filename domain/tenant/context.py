"""Pure domain tenant context based on standard Python ContextVar.

Does not import or depend on web frameworks, allowing safe usage across
threads, async workers, background tasks, CLI commands, and web requests.
"""

from __future__ import annotations

import contextvars
from typing import Optional

_tenant_var: contextvars.ContextVar[Optional[str]] = contextvars.ContextVar('tenant_id', default=None)


class TenantContext:
    """Central tenant context API.

    Usage patterns:
        TenantContext.current() -> Optional[str]
        TenantContext.optional() -> Optional[str]
        TenantContext.require() -> str (raises RuntimeError if missing)
        TenantContext.set(tenant_id)
    """

    @staticmethod
    def current() -> Optional[str]:
        # Check dynamic Flask g if present in active app/request context
        try:
            import sys
            flask_mod = sys.modules.get("flask")
            if flask_mod:
                g_obj = getattr(flask_mod, "g", None)
                if g_obj:
                    val = getattr(g_obj, "tenant_id", None)
                    if val is not None:
                        return val
        except Exception:
            pass
        try:
            return _tenant_var.get()
        except Exception:
            return None

    @staticmethod
    def optional() -> Optional[str]:
        return TenantContext.current()

    @staticmethod
    def require() -> str:
        val = TenantContext.current()
        if not val:
            raise RuntimeError('Tenant id not available in current context')
        return val

    @staticmethod
    def set(tenant_id: Optional[str]):
        _tenant_var.set(tenant_id)


class TenantContextManager:
    """Context manager to temporarily set tenant id in non-request contexts."""

    def __init__(self, tenant_id: Optional[str]):
        self._token = None
        self._tenant_id = tenant_id

    def __enter__(self):
        self._token = _tenant_var.set(self._tenant_id)
        return self

    def __exit__(self, exc_type, exc, tb):
        if self._token is not None:
            _tenant_var.reset(self._token)
