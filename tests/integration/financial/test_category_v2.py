"""
Unit & Integration Tests for Category v2 System
Tests Optimistic Locking, AuditLog creation, and Repository methods.
"""

import pytest
from models import Category, AuditLog, db
from repositories.catalog_repository import CatalogRepository


def test_category_v2_add_and_audit(app, authenticated_client):
    """Kategori ekleme ve AuditLog oluşturulma testi"""
    repo = CatalogRepository()
    cat = repo.add_category(
        name="Test Kategori v2",
        category_type="Gider",
        tenant_id="default",
        code="TEST-001",
        budget_limit=1500.0,
        user_id=1
    )

    assert cat.id is not None
    assert cat.code == "TEST-001"
    assert cat.version == 1
    assert cat.path == f"/{cat.id}/"

    # AuditLog kaydı oluşmuş mu?
    audit = AuditLog.query.filter_by(action='CATEGORY_CREATED', entity_id=str(cat.id)).first()
    assert audit is not None
    assert "TEST-001" in audit.details


def test_category_v2_optimistic_locking(app):
    """Optimistic Locking (Çakışma Önleme) testi"""
    repo = CatalogRepository()
    cat = repo.add_category(
        name="Locking Test Cat",
        category_type="Gelir",
        tenant_id="default",
        user_id=1
    )
    initial_version = cat.version

    # Başarılı güncelleme (Doğru versiyon numarası ile)
    updated = repo.update_category(
        category_id=cat.id,
        new_name="Locking Test Cat Updated",
        new_type="Gelir",
        tenant_id="default",
        version=initial_version,
        user_id=1
    )
    assert updated.version == initial_version + 1
    assert updated.name == "Locking Test Cat Updated"

    # Hatalı güncelleme (Eski versiyon numarası ile çakışma)
    with pytest.raises(ValueError, match="Çakışma Hatası"):
        repo.update_category(
            category_id=cat.id,
            new_name="Conflicting Update",
            new_type="Gelir",
            tenant_id="default",
            version=initial_version,  # Eski versiyon
            user_id=1
        )

