"""Shared financial analysis helpers."""
from shared.decimal_precision import to_decimal


def _apply_tenant(query, model, tenant_id: str | None):
    return query.filter(model.tenant_id == tenant_id) if tenant_id else query


def _as_decimal(value, scale: int = 4):
    return to_decimal(0 if value is None else value, scale=scale)


def _safe_percentage(numerator, denominator) -> float:
    if denominator and denominator > 0:
        return _as_decimal(numerator) / _as_decimal(denominator) * 100
    return 0
