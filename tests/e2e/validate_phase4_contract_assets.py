from __future__ import annotations

import json
import py_compile
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
fixture_path = ROOT / "tests" / "e2e" / "fixtures" / "phase4_fixture_data.json"
fixture_data = json.loads(fixture_path.read_text(encoding="utf-8"))
assert fixture_data["fixture_version"] == "phase4.v1"
assert fixture_data["expected_counts"]["tenant_a"]["transactions"] == 4
assert fixture_data["expected_counts"]["tenant_b"]["transactions"] == 1

from tests.e2e.fixtures.phase4_fixtures import Phase4Fixture  # noqa: E402

fixture = Phase4Fixture(fixture_data)
fixture.assert_expected_counts("e2e_phase4_tenant_a")
fixture.assert_expected_counts("e2e_phase4_tenant_b")

openapi_path = ROOT / "docs" / "api" / "phase4-openapi.yaml"
openapi_data = yaml.safe_load(openapi_path.read_text(encoding="utf-8"))
assert openapi_data["openapi"] == "3.0.3"
expected_paths = {
    "/api/plans/{plan_id}/occurrences",
    "/api/occurrences/{occurrence_id}/pay",
    "/api/occurrences/{occurrence_id}/skip",
    "/api/transactions/{transaction_id}/lineage",
    "/api/transactions/{transaction_id}/adjustments",
    "/api/transactions/{transaction_id}/reversal",
    "/api/ledger-adjustments/{adjustment_id}/audit",
}
assert expected_paths.issubset(openapi_data["paths"])
assert "LedgerAdjustment" in openapi_data["components"]["schemas"]
assert "AuditEvent" in openapi_data["components"]["schemas"]

for relative_path in (
    "tests/e2e/fixtures/phase4_fixtures.py",
    "tests/e2e/mocks/phase4_mock_services.py",
    "tests/e2e/conftest.py",
):
    py_compile.compile(str(ROOT / relative_path), doraise=True)

print("PHASE4_CONTRACT_ASSETS_OK")
print(f"OPENAPI_PATHS={len(openapi_data['paths'])}")
print(f"FIXTURE_TENANTS={len(fixture_data['tenants'])}")
