import os
from pathlib import Path

import pytest

from domain.storage_health.architecture_guard import (
    GuardSeverity,
    check_dependency_shadowing,
    check_governance,
    check_path,
    check_root_drift,
    check_transient_lifecycle,
    run_architecture_guard,
)
from domain.storage_health.lifecycle import governance_for


@pytest.mark.unit
def test_root_drift_is_blocked_without_mutation(tmp_path: Path):
    (tmp_path / "app.py").write_text("placeholder", encoding="utf-8")
    (tmp_path / "unexpected.txt").write_text("fixture", encoding="utf-8")
    issues = check_root_drift(tmp_path, allowed_root_files={"app.py"})
    assert any(item.code == "root_drift" and item.severity is GuardSeverity.BLOCK for item in issues)
    assert (tmp_path / "unexpected.txt").exists()


@pytest.mark.unit
def test_dependency_manifest_at_root_is_shadowing_blocker(tmp_path: Path):
    (tmp_path / "requirements.txt").write_text("fixture", encoding="utf-8")
    issues = check_dependency_shadowing(tmp_path)
    assert issues[0].code == "dependency_shadowing"
    assert issues[0].severity is GuardSeverity.BLOCK


@pytest.mark.unit
def test_path_guard_blocks_absolute_sensitive_and_protected_paths(tmp_path: Path):
    absolute = check_path(tmp_path, tmp_path / "safe.txt")
    sensitive = check_path(tmp_path, ".env")
    protected = check_path(tmp_path, ".venv/Lib/site-packages/example.py")
    assert absolute.code == "absolute_path"
    assert sensitive.code in {"sensitive_path", "protected_path"}
    assert protected.code == "protected_path"


@pytest.mark.unit
def test_governance_guard_distinguishes_pending_policy_from_unknown_owner():
    safe_issues = check_governance(governance_for("cache", "SAFE_AUTO"))
    unknown_issues = check_governance(governance_for("unknown", "REVIEW_REQUIRED"))
    assert any(item.code == "retention_policy_pending" and item.severity is GuardSeverity.WARN for item in safe_issues)
    assert any(item.code == "owner_missing" and item.severity is GuardSeverity.BLOCK for item in unknown_issues)
    assert any(item.code == "retention_unknown" and item.severity is GuardSeverity.BLOCK for item in unknown_issues)


@pytest.mark.unit
def test_transient_guard_reports_stale_file_without_deleting_it(tmp_path: Path):
    transient = tmp_path / "tmp"
    transient.mkdir()
    stale = transient / "old_validation.txt"
    stale.write_text("fixture", encoding="utf-8")
    os.utime(stale, (0, 0))
    issues = check_transient_lifecycle(tmp_path, now_epoch=100, max_age_seconds=10)
    assert issues[0].code == "stale_transient"
    assert issues[0].severity is GuardSeverity.WARN
    assert stale.exists()


@pytest.mark.unit
def test_guard_report_is_explainable_and_explicitly_non_mutating(tmp_path: Path):
    report = run_architecture_guard(
        tmp_path,
        governance=governance_for("cache", "SAFE_AUTO"),
        paths=("safe.txt",),
        allowed_root_files=set(),
        now_epoch=100,
    )
    payload = report.to_dict()
    assert payload["mutation_performed"] is False
    assert "checks" in payload
    assert payload["blocking_count"] == 0
    assert payload["warning_count"] >= 1
