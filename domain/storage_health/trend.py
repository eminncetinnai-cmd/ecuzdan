"""Transparent, metadata-only Storage Health trend calculations."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from domain.storage_health.history import ScanHistoryRecord


@dataclass(frozen=True, slots=True)
class TrendDelta:
    previous_bytes: int
    current_bytes: int
    delta_bytes: int
    percent_change: float | None

    def to_dict(self) -> dict:
        return {
            "previous_bytes": self.previous_bytes,
            "current_bytes": self.current_bytes,
            "delta_bytes": self.delta_bytes,
            "percent_change": self.percent_change,
        }


@dataclass(frozen=True, slots=True)
class StorageTrend:
    available: bool
    reason: str
    previous_history_id: str | None
    current_history_id: str | None
    total: TrendDelta | None
    category_deltas: dict[str, TrendDelta]
    policy_deltas: dict[str, TrendDelta]

    def to_dict(self) -> dict:
        return {
            "available": self.available,
            "reason": self.reason,
            "previous_history_id": self.previous_history_id,
            "current_history_id": self.current_history_id,
            "total": None if self.total is None else self.total.to_dict(),
            "category_deltas": {
                key: value.to_dict() for key, value in sorted(self.category_deltas.items())
            },
            "policy_deltas": {
                key: value.to_dict() for key, value in sorted(self.policy_deltas.items())
            },
        }


def _delta(previous: int, current: int) -> TrendDelta:
    difference = current - previous
    percent = None if previous == 0 else round((difference / previous) * 100, 4)
    return TrendDelta(
        previous_bytes=previous,
        current_bytes=current,
        delta_bytes=difference,
        percent_change=percent,
    )


def _map_delta(
    previous: dict[str, int],
    current: dict[str, int],
) -> dict[str, TrendDelta]:
    keys = set(previous) | set(current)
    return {
        key: _delta(int(previous.get(key, 0)), int(current.get(key, 0)))
        for key in sorted(keys)
    }


def _unavailable(reason: str) -> StorageTrend:
    return StorageTrend(
        available=False,
        reason=reason,
        previous_history_id=None,
        current_history_id=None,
        total=None,
        category_deltas={},
        policy_deltas={},
    )


def compute_storage_trend(histories: Sequence[ScanHistoryRecord]) -> StorageTrend:
    """Compute operational growth from the latest two complete same-scope scans."""
    if len(histories) < 2:
        return _unavailable("insufficient_snapshots")

    ordered = sorted(histories, key=lambda item: (item.scanned_at_epoch, item.history_id))
    previous, current = ordered[-2], ordered[-1]
    if previous.scope != current.scope:
        return _unavailable("scope_mismatch")
    if previous.snapshot_id == current.snapshot_id:
        return _unavailable("same_snapshot")
    if previous.truncated or current.truncated:
        return _unavailable("incomplete_snapshot")
    if previous.errors_count or current.errors_count:
        return _unavailable("snapshot_errors_present")
    if current.scanned_at_epoch <= previous.scanned_at_epoch:
        return _unavailable("non_monotonic_scan_time")

    return StorageTrend(
        available=True,
        reason="two_complete_snapshots",
        previous_history_id=previous.history_id,
        current_history_id=current.history_id,
        total=_delta(previous.total_bytes, current.total_bytes),
        category_deltas=_map_delta(previous.category_bytes, current.category_bytes),
        policy_deltas=_map_delta(previous.policy_bytes, current.policy_bytes),
    )
