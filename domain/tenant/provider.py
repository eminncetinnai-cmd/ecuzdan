"""Tenant provider abstraction.

This module contains a simple Provider class that can be extended to source tenant id from
configuration, environment, or multi-tenant provider services. For now it wraps resolver.resolve_from_request.
"""
from .resolver import resolve_from_request


class TenantProvider:
    """Simple provider that resolves tenant id on demand."""

    def __init__(self, fallback=None):
        self.fallback = fallback

    def get_tenant(self):
        t = resolve_from_request()
        if t:
            return t
        return self.fallback
