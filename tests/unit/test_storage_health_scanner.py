"""Observe Core tests; no database, secrets, hashing or filesystem mutation."""


import pytest

from domain.storage_health.dto import StorageObservationDTO, StorageScanDTO
from domain.storage_health.policy import PolicyClass
from domain.storage_health.services.classifier import StorageClassifier
from domain.storage_health.services.protected import ProtectedResourceDetector
from domain.storage_health.services.scanner import StorageScanner


@pytest.mark.unit
def test_classifier_protects_sqlite_anchors_and_canonical_tree(tmp_path):
    classifier = StorageClassifier(tmp_path)

    category, policy, reason = classifier.classify(tmp_path / "e_cuzdan_v15.db")
    assert category == "database"
    assert policy == PolicyClass.PROTECTED
    assert reason == "active_sqlite_anchor"

    category, policy, _ = classifier.classify(tmp_path / "configuration" / "dependencies" / "requirements.txt")
    assert category == "configuration"
    assert policy == PolicyClass.PROTECTED

    category, policy, _ = classifier.classify(tmp_path / ".venv" / "Lib" / "site-packages" / "flask.py")
    assert category == "runtime"
    assert policy == PolicyClass.PROTECTED


@pytest.mark.unit
def test_classifier_marks_regenerable_cache_safe_auto(tmp_path):
    classifier = StorageClassifier(tmp_path)
    category, policy, reason = classifier.classify(tmp_path / "__pycache__" / "module.pyc")

    assert category == "cache"
    assert policy == PolicyClass.SAFE_AUTO
    assert reason == "regenerable_cache"


@pytest.mark.unit
def test_backup_and_unknown_resources_require_review(tmp_path):
    classifier = StorageClassifier(tmp_path)

    _, backup_policy, backup_reason = classifier.classify(tmp_path / "backups" / "old.zip")
    _, unknown_policy, unknown_reason = classifier.classify(tmp_path / "unclassified.bin")

    assert backup_policy == PolicyClass.REVIEW_REQUIRED
    assert backup_reason == "backup_retention_and_integrity_review"
    assert unknown_policy == PolicyClass.REVIEW_REQUIRED
    assert unknown_reason == "unclassified_resource"


@pytest.mark.unit
def test_scanner_reads_metadata_and_produces_category_totals(tmp_path):
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "module.py").write_text("not read by scanner", encoding="utf-8")
    (tmp_path / "__pycache__").mkdir()
    (tmp_path / "__pycache__" / "module.pyc").write_bytes(b"cache")
    (tmp_path / "backups").mkdir()
    (tmp_path / "backups" / "old.zip").write_bytes(b"backup")

    scan = StorageScanner(tmp_path, max_files=100, max_seconds=5).scan()

    assert scan.files_scanned == 3
    assert scan.total_bytes == len("not read by scanner") + len(b"cache") + len(b"backup")
    assert scan.category_bytes["cache"] >= len(b"cache")
    assert scan.category_bytes["backups"] >= len(b"backup")
    assert scan.policy_bytes[PolicyClass.SAFE_AUTO.value] >= len(b"cache")
    assert scan.policy_bytes[PolicyClass.REVIEW_REQUIRED.value] >= len(b"backup")
    assert scan.errors == ()
    assert scan.truncated is False


@pytest.mark.unit
def test_protected_detector_hides_sensitive_paths_from_dto(tmp_path):
    detector = ProtectedResourceDetector(tmp_path)
    policy, reason = detector.explain(tmp_path / ".env")
    assert policy == PolicyClass.PROTECTED
    assert reason == "sensitive_or_credential_name"

    from domain.storage_health.services.scanner import StorageObservation

    dto = StorageObservationDTO.from_observation(
        StorageObservation(
            relative_path="instance/.env/client_secret.json",
            category="unknown",
            policy_class=PolicyClass.PROTECTED.value,
            reason="sensitive_or_credential_name",
            bytes=12,
            modified_epoch=None,
        )
    )
    assert dto.relative_path == "<protected-resource>"


@pytest.mark.unit
def test_scan_dto_contains_no_absolute_project_root(tmp_path):
    scan = StorageScanner(tmp_path).scan()
    dto = StorageScanDTO.from_scan(scan).to_dict()

    assert str(tmp_path) not in str(dto)
    assert set(dto["policy_classes"]) == {item.value for item in PolicyClass}
