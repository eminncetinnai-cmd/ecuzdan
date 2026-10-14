"""Unit & Disposable Environment Integration Tests for Runtime Bootstrap Suite.

Tests:
  - Scenario A: Healthy machine preflight check
  - Scenario B: Missing .venv detection and creation
  - Scenario C: Missing runtime dependencies detection
  - Scenario D: Python discovery and compatibility validation
  - Scenario E: Application process & port management
  - Scenario F: Configuration validation readiness
  - Scenario G: Reporter secret masking and diagnostic formatting
"""

from __future__ import annotations

from unittest.mock import patch

import pytest

from scripts.runtime.bootstrap import RuntimeBootstrap
from scripts.runtime.configuration_validator import ConfigurationValidator
from scripts.runtime.dependency_manager import DependencyManager
from scripts.runtime.process_manager import ProcessManager
from scripts.runtime.python_discovery import PythonDiscoveryEngine
from scripts.runtime.runtime_reporter import RuntimeReporter, mask_sensitive_text


@pytest.mark.unit
def test_reporter_masks_sensitive_text():
    raw = "Failed connecting with token=secret_token_12345 and password: my_db_password"
    masked = mask_sensitive_text(raw)
    assert "secret_token_12345" not in masked
    assert "my_db_password" not in masked
    assert "[REDACTED]" in masked


@pytest.mark.unit
def test_python_discovery_validates_compatibility():
    engine = PythonDiscoveryEngine(min_version=(3, 13, 0), max_version=(3, 14, 0))
    res = engine.discover()
    assert res.executable != ""
    assert res.version_str != ""
    assert res.is_compatible is True
    assert res.has_venv is True


@pytest.mark.unit
def test_python_discovery_rejects_incompatible_version():
    engine = PythonDiscoveryEngine(min_version=(3, 99, 0), max_version=(3, 100, 0))
    res = engine.discover()
    assert res.is_compatible is False
    assert "E-Cüzdan requires Python" in res.error_message


@pytest.mark.unit
def test_configuration_validator_healthy_repo(tmp_path):
    (tmp_path / "app.py").write_text("# app", encoding="utf-8")
    (tmp_path / "config.py").write_text("# config", encoding="utf-8")
    (tmp_path / "models.py").write_text("# models", encoding="utf-8")
    (tmp_path / "e_cuzdan_v15.db").write_text("sqlite", encoding="utf-8")
    (tmp_path / "logs").mkdir()

    validator = ConfigurationValidator(repo_root=tmp_path)
    res = validator.validate()
    assert res.is_ready is True
    assert len(res.errors) == 0


@pytest.mark.unit
def test_configuration_validator_detects_missing_entrypoint(tmp_path):
    validator = ConfigurationValidator(repo_root=tmp_path)
    res = validator.validate()
    assert res.is_ready is False
    assert any("app.py" in err for err in res.errors)


@pytest.mark.unit
def test_process_manager_handles_free_port():
    proc = ProcessManager(port=59999)  # High unused port
    stat = proc.inspect_runtime()
    assert stat.is_port_in_use is False
    assert stat.is_our_app_running is False


@pytest.mark.unit
def test_process_manager_detects_running_app():
    proc = ProcessManager(port=5000)
    with patch.object(proc, "is_port_bound", return_value=True):
        with patch.object(proc, "check_app_health", return_value=True):
            stat = proc.inspect_runtime()
            assert stat.is_port_in_use is True
            assert stat.is_our_app_running is True


@pytest.mark.unit
def test_process_manager_detects_port_conflict():
    proc = ProcessManager(port=5000)
    with patch.object(proc, "is_port_bound", return_value=True):
        with patch.object(proc, "check_app_health", return_value=False):
            stat = proc.inspect_runtime()
            assert stat.is_port_in_use is True
            assert stat.is_our_app_running is False


@pytest.mark.unit
def test_dependency_manager_authority_discovery(tmp_path):
    dep_dir = tmp_path / "configuration" / "dependencies"
    dep_dir.mkdir(parents=True)
    lock_file = dep_dir / "requirements-runtime-lock.txt"
    lock_file.write_text("flask==3.1.3\n", encoding="utf-8")

    mgr = DependencyManager(repo_root=tmp_path, venv_python="python")
    found = mgr.discover_authority_manifest()
    assert found == lock_file


@pytest.mark.unit
def test_runtime_bootstrap_check_only_lifecycle():
    reporter = RuntimeReporter()
    bootstrap = RuntimeBootstrap(reporter=reporter)
    exit_code = bootstrap.run(check_only=True)
    assert exit_code == 0
