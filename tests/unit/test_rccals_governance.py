"""RCCALS (Repository Change Control & Artifact Lifecycle System) Unit Tests.

Verifies:
  - Change Preflight Engine decision logic
  - Root directory protection and blocked prefixes
  - Temporary artifact confinement to .work/
  - Naming policy enforcement and forbidden patterns
  - Unauthorized directory detection
  - Duplicate component prevention
  - .work lifecycle and retention auditor
  - Post-change governance audit pipeline
"""

from __future__ import annotations

import pytest

from scripts.governance.architecture_gate import ArchitectureGate
from scripts.governance.change_preflight import (
    ArtifactIntent,
    ChangePreflightEngine,
    PreflightDecision,
)
from scripts.governance.duplicate_prevention import (
    DuplicatePreventionScanner,
    DuplicateRiskStatus,
)
from scripts.governance.post_change_governance import (
    PostChangeGovernanceAuditor,
    PostChangeStatus,
)
from scripts.governance.work_lifecycle import (
    WorkCategory,
    WorkLifecycleAuditor,
)


@pytest.mark.unit
def test_preflight_allows_valid_domain_artifact(tmp_path):
    engine = ChangePreflightEngine(repo_root=tmp_path)
    intent = ArtifactIntent(
        path="domain/portfolio/services/rebalancing_service.py",
        purpose="Portfolio rebalancing business logic",
        artifact_type="source",
        target_layer="domain",
    )
    result = engine.evaluate([intent])
    assert result.decision == PreflightDecision.ALLOW
    assert result.is_allowed is True
    assert len(result.notices) == 0


@pytest.mark.unit
def test_preflight_blocks_root_pollution_forbidden_prefix(tmp_path):
    engine = ChangePreflightEngine(repo_root=tmp_path)
    for bad_name in ["tmp_test.py", "debug_auth.py", "probe_calc.py", "analysis_perf.py", "copy_models.py"]:
        intent = ArtifactIntent(path=bad_name)
        result = engine.evaluate([intent])
        assert result.decision == PreflightDecision.BLOCK
        assert any(n.category == "ROOT_POLLUTION" for n in result.notices)


@pytest.mark.unit
def test_preflight_blocks_unauthorized_root_file(tmp_path):
    engine = ChangePreflightEngine(repo_root=tmp_path)
    intent = ArtifactIntent(path="random_utility_file.py")
    result = engine.evaluate([intent])
    assert result.decision == PreflightDecision.BLOCK
    assert any(n.category == "ROOT_POLLUTION" for n in result.notices)


@pytest.mark.unit
def test_preflight_blocks_temporary_artifact_outside_work(tmp_path):
    engine = ChangePreflightEngine(repo_root=tmp_path)
    intent = ArtifactIntent(
        path="domain/analysis/services/probe_market_rate.py",
        artifact_type="temporary",
    )
    result = engine.evaluate([intent])
    assert result.decision == PreflightDecision.BLOCK
    assert any(n.category == "TEMP_ARTIFACT_OUTSIDE_WORKSPACE" for n in result.notices)


@pytest.mark.unit
def test_preflight_allows_temporary_artifact_inside_work(tmp_path):
    engine = ChangePreflightEngine(repo_root=tmp_path)
    intent = ArtifactIntent(
        path=".work/probes/probe_market_rate.py",
        artifact_type="temporary",
    )
    result = engine.evaluate([intent])
    assert result.decision == PreflightDecision.ALLOW


@pytest.mark.unit
def test_preflight_blocks_forbidden_naming_patterns(tmp_path):
    engine = ChangePreflightEngine(repo_root=tmp_path)
    bad_paths = [
        "domain/portfolio/services/portfolio_v2.py",
        "domain/portfolio/services/portfolio_final.py",
        "application/users/user_service_backup.py",
    ]
    for bad_path in bad_paths:
        intent = ArtifactIntent(path=bad_path)
        result = engine.evaluate([intent])
        assert result.decision == PreflightDecision.BLOCK
        assert any(n.category == "INVALID_NAMING" for n in result.notices)


@pytest.mark.unit
def test_preflight_blocks_unauthorized_top_directory(tmp_path):
    engine = ChangePreflightEngine(repo_root=tmp_path)
    intent = ArtifactIntent(path="custom_experimental_folder/my_module.py")
    result = engine.evaluate([intent])
    assert result.decision == PreflightDecision.BLOCK
    assert any(n.category == "UNAUTHORIZED_DIRECTORY" for n in result.notices)


@pytest.mark.unit
def test_duplicate_prevention_detects_existing_component(tmp_path):
    # Setup dummy existing file
    domain_dir = tmp_path / "domain" / "portfolio"
    domain_dir.mkdir(parents=True)
    existing_file = domain_dir / "calculator.py"
    existing_file.write_text("class AssetValuationCalculator:\n    pass\n", encoding="utf-8")

    scanner = DuplicatePreventionScanner(repo_root=tmp_path)
    # Check intent for creating same stem in same layer
    res = scanner.check_intent("domain/analysis/calculator.py")
    assert res.status == DuplicateRiskStatus.EXISTING_COMPONENT_REUSE

    # Check intent for creating same class name
    res2 = scanner.check_intent("domain/valuation/asset_calc.py", component_names=["AssetValuationCalculator"])
    assert res2.status == DuplicateRiskStatus.POSSIBLE_DUPLICATE


@pytest.mark.unit
def test_work_lifecycle_auditor_categorizes_artifacts(tmp_path):
    work_dir = tmp_path / ".work"
    (work_dir / "investigations").mkdir(parents=True)
    (work_dir / "experiments").mkdir(parents=True)
    (work_dir / "investigations" / "test_report.json").write_text("{}", encoding="utf-8")
    (work_dir / "experiments" / "test_exp.py").write_text("print(1)", encoding="utf-8")

    auditor = WorkLifecycleAuditor(repo_root=tmp_path)
    report = auditor.audit()
    assert report.total_files == 2
    assert report.category_counts[WorkCategory.INVESTIGATIONS.value] == 1
    assert report.category_counts[WorkCategory.EXPERIMENTS.value] == 1


@pytest.mark.unit
def test_architecture_gate_detects_unauthorized_top_dir(tmp_path):
    unauthorized = tmp_path / "unauthorized_legacy_dir"
    unauthorized.mkdir()
    (unauthorized / "file.txt").write_text("legacy", encoding="utf-8")

    gate = ArchitectureGate(repo_root=tmp_path)
    rep = gate.scan()
    assert any(v.category == "UNAUTHORIZED_DIRECTORY" for v in rep.violations)


@pytest.mark.unit
def test_post_change_governance_runs_audit(tmp_path):
    auditor = PostChangeGovernanceAuditor(repo_root=tmp_path)
    report = auditor.run_audit()
    assert report.status in (PostChangeStatus.PASS, PostChangeStatus.WARN)
