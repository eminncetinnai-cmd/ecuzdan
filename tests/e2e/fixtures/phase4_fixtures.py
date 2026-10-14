"""Phase 4 için deterministic, tenant-scoped E2E fixture yardımcıları."""

from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path
from typing import Any

FIXTURE_PATH = Path(__file__).with_name("phase4_fixture_data.json")


class Phase4Fixture:
    """JSON fixture verisini testler arasında güvenli ve izole biçimde sunar."""

    def __init__(self, data: dict[str, Any]):
        self.data = deepcopy(data)

    @classmethod
    def load(cls, path: Path | None = None) -> "Phase4Fixture":
        fixture_path = path or FIXTURE_PATH
        with fixture_path.open("r", encoding="utf-8") as fixture_file:
            return cls(json.load(fixture_file))

    def tenant(self, tenant_id: str) -> dict[str, Any]:
        for tenant in self.data["tenants"]:
            if tenant["id"] == tenant_id:
                return deepcopy(tenant)
        raise KeyError(f"Fixture tenant bulunamadı: {tenant_id}")

    def records(self, collection: str, tenant_id: str) -> list[dict[str, Any]]:
        return [
            deepcopy(record)
            for record in self.data.get(collection, [])
            if record.get("tenant_id") == tenant_id
        ]

    def record(self, collection: str, record_id: int, tenant_id: str) -> dict[str, Any]:
        for record in self.data.get(collection, []):
            if record.get("id") == record_id and record.get("tenant_id") == tenant_id:
                return deepcopy(record)
        raise KeyError(f"Fixture kaydı bulunamadı: {collection}/{record_id}")

    def expected_counts(self, tenant_id: str) -> dict[str, int]:
        key = "tenant_a" if tenant_id.endswith("_a") else "tenant_b"
        return deepcopy(self.data["expected_counts"][key])

    def marker(self, tenant_id: str) -> str:
        return self.tenant(tenant_id)["marker"]

    def snapshot(self, tenant_id: str) -> dict[str, int]:
        collections = (
            "plans",
            "occurrences",
            "payments",
            "transactions",
            "ledger_adjustments",
            "audit_events",
        )
        return {collection: len(self.records(collection, tenant_id)) for collection in collections}

    def assert_expected_counts(self, tenant_id: str) -> None:
        actual = self.snapshot(tenant_id)
        expected = self.expected_counts(tenant_id)
        if actual != expected:
            raise AssertionError(f"Fixture adetleri uyuşmuyor: actual={actual}, expected={expected}")


# Pytest fixture fonksiyonları mevcut tests/e2e/conftest.py içine kopyalanmadan da
# doğrudan test modüllerinden import edilebilir.
def phase4_fixture() -> Phase4Fixture:
    return Phase4Fixture.load()


def phase4_tenant_a() -> str:
    return "e2e_phase4_tenant_a"


def phase4_tenant_b() -> str:
    return "e2e_phase4_tenant_b"
