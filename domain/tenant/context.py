import contextvars
from typing import Optional

try:
    # Flask imports only used at runtime when available
    from flask import g, has_request_context, request
except Exception:
    has_request_context = None
    g = None
    request = None

_tenant_var: contextvars.ContextVar[Optional[str]] = contextvars.ContextVar('tenant_id', default=None)


class TenantContext:
    """Central tenant context API.

    Usage patterns:
        TenantContext.current() -> Optional[str]
        TenantContext.optional() -> Optional[str]
        TenantContext.require() -> str (raises RuntimeError if missing)
        TenantContext.set(tenant_id)

    This implementation prefers Flask's `g` when a request context exists, otherwise uses a ContextVar so background workers and CLI can set the tenant.
    """

    @staticmethod
    def current() -> Optional[str]:
        # Prefer Flask request context if available
        try:
            if has_request_context() and g is not None:
                # allow both attribute and mapping access
                if hasattr(g, 'tenant_id'):
                    return getattr(g, 'tenant_id')
                # g may act like dict in some contexts
                val = None
                try:
                    val = g.get('tenant_id')
                except Exception:
                    val = None
                if val is not None:
                    return val
        except Exception:
            # If Flask not available or error, continue to contextvar
            pass
        # Fallback to context var
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
        # If in Flask request context, set on g; otherwise set contextvar
        try:
            if has_request_context() and g is not None:
                try:
                    setattr(g, 'tenant_id', tenant_id)
                    return
                except Exception:
                    pass
        except Exception:
            pass
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
