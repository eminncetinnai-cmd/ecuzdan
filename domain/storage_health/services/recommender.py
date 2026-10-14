"""Non-destructive recommendation generation from an Observe scan."""

from __future__ import annotations

from pathlib import Path

from domain.storage_health.models import CleanupCandidate, RecommendationSet
from domain.storage_health.policy import PolicyClass
from domain.storage_health.services.scanner import StorageScan
from domain.storage_health.services.snapshot import build_snapshot_fingerprint


class StorageRecommender:
    """Turn an immutable metadata scan into reviewable candidate DTOs."""

    def __init__(self, project_root: str | Path):
        self.root = Path(project_root).resolve()

    def recommend(self, scan: StorageScan) -> RecommendationSet:
        fingerprint = build_snapshot_fingerprint(scan)
        candidates = []
        for observation in scan.observations:
            if observation.is_directory or observation.bytes <= 0:
                continue
            if observation.policy_class == PolicyClass.PROTECTED.value:
                continue
            candidates.append(
                CleanupCandidate.from_observation(
                    observation,
                    snapshot_token=fingerprint.token,
                )
            )
        candidates.sort(key=lambda item: (-item.reclaimable_bytes, item.relative_path))
        return RecommendationSet(
            scan=scan,
            snapshot_token=fingerprint.token,
            candidates=tuple(candidates),
        )
