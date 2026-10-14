"""Unit tests for Storage Health safe cleanup executor and application service."""

import tempfile
from pathlib import Path

import pytest

from application.storage_health.service import StorageHealthApplicationService
from domain.storage_health.cleanup_executor import (
    CleanupExecutor,
    _validate_relative_path,
)


@pytest.mark.unit
def test_validate_relative_path_blocks_traversal():
    root = Path("/dummy/app")
    ok, reason, _ = _validate_relative_path(root, "../../etc/passwd")
    assert not ok
    assert reason == "path_traversal"


@pytest.mark.unit
def test_validate_relative_path_blocks_database_files():
    root = Path("/dummy/app")
    ok, reason, _ = _validate_relative_path(root, "instance/app.db")
    assert not ok
    assert "blocked_suffix" in reason


@pytest.mark.unit
def test_validate_relative_path_blocks_source_code():
    root = Path("/dummy/app")
    for f in ["app.py", "routes/auth.py", "domain/model.py"]:
        ok, reason, _ = _validate_relative_path(root, f)
        assert not ok


@pytest.mark.unit
def test_validate_relative_path_blocks_logs():
    root = Path("/dummy/app")
    ok, reason, _ = _validate_relative_path(root, "logs/security.log")
    assert not ok
    assert "blocked_suffix" in reason or "blocked_part" in reason


@pytest.mark.unit
def test_validate_relative_path_blocks_unallowlisted_parents():
    root = Path("/dummy/app")
    ok, reason, _ = _validate_relative_path(root, "uploads/user_avatar.png")
    assert not ok
    assert "not_allowlisted_parent" in reason


@pytest.mark.unit
def test_validate_relative_path_allows_pycache():
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        pycache = root / "__pycache__"
        pycache.mkdir()
        pyc = pycache / "test.cpython-313.pyc"
        pyc.write_bytes(b"\x00" * 20)

        ok, reason, resolved = _validate_relative_path(root, "__pycache__/test.cpython-313.pyc")
        assert ok
        assert resolved == pyc


@pytest.mark.unit
def test_cleanup_executor_removes_safe_auto_candidates():
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        pycache = root / "__pycache__"
        pycache.mkdir()
        file1 = pycache / "a.pyc"
        file2 = pycache / "b.pyc"
        file1.write_bytes(b"x" * 50)
        file2.write_bytes(b"y" * 100)

        executor = CleanupExecutor(root)
        candidates = [
            {
                "candidate_id": "c1",
                "relative_path": "__pycache__/a.pyc",
                "policy_class": "SAFE_AUTO",
                "execute_eligible": True,
            },
            {
                "candidate_id": "c2",
                "relative_path": "__pycache__/b.pyc",
                "policy_class": "SAFE_AUTO",
                "execute_eligible": True,
            },
            {
                "candidate_id": "c3_protected",
                "relative_path": "app.py",
                "policy_class": "SAFE_AUTO",
                "execute_eligible": True,
            },
        ]

        summary = executor.execute(candidates, selected_ids={"c1", "c3_protected"})
        assert len(summary.executed) == 1
        assert summary.executed[0].candidate_id == "c1"
        assert summary.bytes_freed == 50
        assert not file1.exists()
        assert file2.exists()  # Not selected, so kept

        # c3_protected must have been skipped due to path validation
        assert any(s.candidate_id == "c3_protected" for s in summary.skipped)


@pytest.mark.unit
def test_service_execute_cleanup_validation():
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        service = StorageHealthApplicationService(root)

        # Calling without cache raises ValueError
        with pytest.raises(ValueError, match="no_cached_scan"):
            service.execute_cleanup(
                plan_hash="invalid",
                snapshot_id="invalid",
                candidate_ids=["c1"],
            )
