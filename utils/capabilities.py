"""Canonical authorization capabilities for platform and tenant features.

Role checks remain supported for backwards compatibility, while privileged
features use these capability names so UI and backend enforce one policy.
"""

from __future__ import annotations

from enum import StrEnum
from typing import Any


class Capability(StrEnum):
    """Stable capability identifiers used by routes, services and templates."""

    FULL_PLATFORM_ACCESS = "platform.full_access"
    MONITORING_VIEW = "monitoring.view"
    STORAGE_HEALTH_VIEW = "storage_health.view"
    DEMO_DATA_WRITE = "demo_data.write"
    PLATFORM_BACKUP = "platform.backup"
    ADMIN_USER_MANAGEMENT = "admin.user_management"
    ADMIN_TENANT_MANAGEMENT = "admin.tenant_management"
    OCCURRENCE_PAY = "planning.occurrence_pay"
    OCCURRENCE_SKIP = "planning.occurrence_skip"
    LEDGER_ADJUST = "ledger.adjust"
    LEDGER_REVERSE = "ledger.reverse"
    LEDGER_AUDIT_READ = "ledger.audit_read"


ALL_CAPABILITIES = frozenset(capability.value for capability in Capability)


def _metadata_capabilities(user: Any) -> frozenset[str]:
    """Read capabilities from the redeemed special-code metadata.

    Configuration lookup is intentionally lazy to avoid importing the service
    while SQLAlchemy models are still being imported.
    """
    if user is None or not getattr(user, "special_code_used_at", None):
        return frozenset()

    code = getattr(user, "special_code", None)
    if not code:
        return frozenset()

    try:
        from domain.users.services.special_code_service import get_special_code_service

        service = get_special_code_service()
        resolver = getattr(service, 'get_code_info_for_stored', service.get_code_info)
        info = resolver(code) or {}
    except (OSError, TypeError, ValueError):
        return frozenset()

    metadata = info.get("metadata") or {}
    if metadata.get("grants_all_capabilities") is True:
        return ALL_CAPABILITIES

    configured = metadata.get("capabilities") or []
    return frozenset(str(item) for item in configured)


def has_full_platform_access(user: Any) -> bool:
    """Return whether a user has Emin-level platform capabilities."""
    if user is None:
        return False
    if getattr(user, "is_super_admin", False):
        return True
    if getattr(user, "role", None) == "sistem_yoneticisi":
        return True
    uname = getattr(user, "username", "") or ""
    uemail = getattr(user, "email", "") or ""
    if str(uname).lower() in ("emin", "eminncetinn@gmail.com", "eminncetinn.ai@gmail.com"):
        return True
    if str(uemail).lower() in ("eminncetinn@gmail.com", "eminncetinn.ai@gmail.com"):
        return True
    return Capability.FULL_PLATFORM_ACCESS.value in _metadata_capabilities(user)


def has_capability(user: Any, capability: str | Capability) -> bool:
    """Evaluate a capability with full-platform inheritance."""
    if user is None:
        return False
    name = capability.value if isinstance(capability, Capability) else str(capability)
    if has_full_platform_access(user):
        return True
    if getattr(user, "role", None) in ("sistem_yoneticisi", "yonetici", "admin"):
        if name in (Capability.STORAGE_HEALTH_VIEW.value, Capability.MONITORING_VIEW.value):
            return True
    return name in _metadata_capabilities(user)
