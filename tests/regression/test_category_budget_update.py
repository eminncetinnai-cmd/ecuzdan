from __future__ import annotations

from models import Category, db


def _add_category(**overrides):
    values = {
        "code": "GDR-7999",
        "name": "Standart Test Gideri",
        "type": "Gider",
        "tenant_id": None,
        "budget_limit": 100,
        "version": 1,
        "is_active": True,
    }
    values.update(overrides)
    category = Category(**values)
    db.session.add(category)
    db.session.commit()
    return category


def test_standard_category_allows_only_monthly_budget_update(app, authenticated_client):
    category = _add_category()
    category_id = category.id
    original_name = category.name
    original_type = category.type
    original_code = category.code
    original_version = category.version

    response = authenticated_client.post(
        f"/update_category/{category_id}",
        data={
            "name": original_name,
            "type": original_type,
            "code": original_code,
            "budget_limit": "250,75",
            "version": str(original_version),
        },
        follow_redirects=False,
    )

    assert response.status_code == 302
    refreshed = db.session.get(Category, category_id)
    assert refreshed.name == "Standart Test Gideri"
    assert refreshed.type == "Gider"
    assert refreshed.code == "GDR-7999"
    assert str(refreshed.budget_limit) == "250.7500"
    assert refreshed.version == 2


def test_standard_category_core_fields_and_delete_remain_protected(app, authenticated_client):
    category = _add_category()
    category_id = category.id
    original_version = category.version

    update_response = authenticated_client.post(
        f"/update_category/{category_id}",
        data={
            "name": "Yetkisiz Değişiklik",
            "type": "Gelir",
            "code": "GLR-6999",
            "budget_limit": "300",
            "version": str(original_version),
        },
        follow_redirects=False,
    )
    delete_response = authenticated_client.delete(
        f"/delete_category/{category_id}",
        headers={"X-Requested-With": "XMLHttpRequest"},
    )

    assert update_response.status_code == 302
    assert delete_response.status_code == 400
    assert delete_response.get_json()["status"] == "error"
    refreshed = db.session.get(Category, category_id)
    assert refreshed.name == "Standart Test Gideri"
    assert refreshed.type == "Gider"
    assert refreshed.code == "GDR-7999"
    assert str(refreshed.budget_limit) == "100.0000"
    assert refreshed.is_active is True


def test_custom_category_update_remains_full_editable(app, authenticated_client):
    category = _add_category(
        code="CUS-0001",
        name="Özel Kategori",
        tenant_id="default",
        budget_limit=50,
    )
    category_id = category.id
    original_version = category.version

    response = authenticated_client.post(
        f"/update_category/{category_id}",
        data={
            "name": "Özel Kategori Güncel",
            "type": "Gider",
            "code": "CUS-0002",
            "budget_limit": "75.50",
            "version": str(original_version),
        },
        follow_redirects=False,
    )

    assert response.status_code == 302
    refreshed = db.session.get(Category, category_id)
    assert refreshed.name == "Özel Kategori Güncel"
    assert refreshed.code == "CUS-0002"
    assert str(refreshed.budget_limit) == "75.5000"
    assert refreshed.version == 2
