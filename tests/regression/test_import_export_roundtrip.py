from __future__ import annotations

import json
from decimal import Decimal

import pytest


@pytest.mark.regression
def test_sample_financial_data_round_trips_without_live_mutation(app):
    from infrastructure.backup.validation import BackupValidationService
    from infrastructure.database.management import (
        export_database_to_json,
        import_database_from_json,
    )
    from models import Asset, AssetSector, AssetType, Category, RecurringPlan, Transaction, db

    with app.app_context():
        tenant_id = "default"
        category = Category.query.filter_by(name="Maaş").first()
        asset_type = AssetType.query.filter_by(name="Hisse Senedi").first()
        sector = AssetSector.query.filter_by(name="Teknoloji").first()
        assert category is not None
        assert asset_type is not None
        assert sector is not None

        before_counts = {
            "transactions": Transaction.query.filter_by(tenant_id=tenant_id).count(),
            "assets": Asset.query.filter_by(tenant_id=tenant_id).count(),
            "plans": RecurringPlan.query.filter_by(tenant_id=tenant_id).count(),
        }

        asset = Asset(
            type=asset_type.name,
            name="E2E Roundtrip Hisse",
            value=Decimal("12500.0000"),
            description="İzole import/export round-trip fixture",
            purchase_date="2026-01-15",
            purchase_cost=Decimal("10000.0000"),
            quantity=Decimal("100.0000"),
            unit_price=Decimal("125.0000"),
            currency="TRY",
            symbol="E2E.RT",
            risk_level="Orta",
            liquidity="Likid",
            sector_id=sector.id,
            tenant_id=tenant_id,
        )
        db.session.add(asset)
        db.session.flush()

        plan = RecurringPlan(
            name="E2E Roundtrip Plan",
            category=category.name,
            flow_type="Gelir",
            amount=Decimal("2500.0000"),
            installments=6,
            payment_day=15,
            start_date="2026-01-01",
            tenant_id=tenant_id,
        )
        transaction = Transaction(
            date="2026-02-15",
            category=category.name,
            description="E2E round-trip örnek gelir",
            type="Gelir",
            status="Ödendi",
            amount=Decimal("2500.0000"),
            tenant_id=tenant_id,
            source_type="manual",
        )
        db.session.add_all([plan, transaction])
        db.session.commit()

        created_ids = {"asset": asset.id, "plan": plan.id, "transaction": transaction.id}
        exported = export_database_to_json(encrypt=False)
        payload = json.loads(exported)
        valid, validation_message = BackupValidationService().validate_backup_compatibility(payload)
        assert valid, validation_message
        assert any(item["id"] == asset.id for item in payload["assets"])
        assert any(item["id"] == plan.id for item in payload["recurring_plans"])
        assert any(item["id"] == transaction.id for item in payload["transactions"])

        success, import_message = import_database_from_json(exported)
        assert success, import_message

        assert Transaction.query.filter_by(tenant_id=tenant_id).count() == before_counts["transactions"] + 1
        assert Asset.query.filter_by(tenant_id=tenant_id).count() == before_counts["assets"] + 1
        assert RecurringPlan.query.filter_by(tenant_id=tenant_id).count() == before_counts["plans"] + 1
        assert db.session.get(Asset, created_ids["asset"]).value == Decimal("12500.0000")
        assert db.session.get(RecurringPlan, created_ids["plan"]).amount == Decimal("2500.0000")
        assert db.session.get(Transaction, created_ids["transaction"]).amount == Decimal("2500.0000")


@pytest.mark.regression
def test_encrypted_full_export_import_requires_correct_password(app):
    from infrastructure.database.management import (
        export_database_to_json,
        import_database_from_json,
    )

    with app.app_context():
        encrypted = export_database_to_json(encrypt=True, password="roundtrip-secret")
        envelope = json.loads(encrypted)
        assert envelope["encrypted"] is True
        assert envelope["schema_version"] == "v25.2"

        wrong_password_success, _ = import_database_from_json(
            encrypted,
            password="wrong-password",
        )
        assert wrong_password_success is False

        success, message = import_database_from_json(
            encrypted,
            password="roundtrip-secret",
        )
        assert success, message


@pytest.mark.regression
def test_tenant_export_does_not_include_other_tenant_financial_rows(app):
    from infrastructure.export.export_service import ExportService
    from models import Tenant, Transaction, User, db

    with app.app_context():
        default_user = User.query.filter_by(username="testuser").first()
        other_tenant = Tenant(id="export-isolation", name="Export Isolation Tenant")
        other_user = User(
            username="export-isolation-user",
            password="test-password-hash",
            role="kullanici",
            tenant_id=other_tenant.id,
        )
        other_transaction = Transaction(
            date="2026-03-01",
            category="Maaş",
            description="Başka tenant işlemi",
            type="Gelir",
            status="Ödendi",
            amount=Decimal("9999.0000"),
            tenant_id=other_tenant.id,
        )
        db.session.add_all([other_tenant, other_user, other_transaction])
        db.session.commit()

        payload = json.loads(ExportService().export_tenant_json(user_id=default_user.id))
        assert payload["tenant_id"] == "default"
        assert all(row["tenant_id"] == "default" for row in payload["transactions"])
        assert all(row["tenant_id"] == "default" for row in payload["recurring_plans"])
        assert all(row["tenant_id"] == "default" for row in payload["assets"])
        assert all(row["description"] != "Başka tenant işlemi" for row in payload["transactions"])


@pytest.mark.regression
def test_platform_export_and_multipart_import_routes_round_trip_in_isolated_app(app, client):
    import io

    from models import User

    platform_user = User.query.filter_by(username="emin").first()
    assert platform_user is not None
    with client.session_transaction() as session:
        session["user_id"] = platform_user.id
        session["username"] = platform_user.username

    export_response = client.get("/export_db_json")
    assert export_response.status_code == 200
    assert export_response.content_type.startswith("application/json")
    assert "attachment" in export_response.headers.get("Content-Disposition", "")

    import_response = client.post(
        "/import_db_json",
        data={"db_file": (io.BytesIO(export_response.data), "e_cuzdan_roundtrip.json")},
        content_type="multipart/form-data",
        follow_redirects=False,
    )
    assert import_response.status_code in {302, 303}


@pytest.mark.regression
def test_invalid_record_rolls_back_entire_import_atomically(app):
    from infrastructure.database.management import (
        export_database_to_json,
        import_database_from_json,
    )
    from models import Transaction, db

    with app.app_context():
        payload = json.loads(export_database_to_json(encrypt=False))
        before_count = Transaction.query.filter_by(tenant_id="default").count()
        payload["transactions"].append(
            {
                "id": None,
                "tenant_id": "default",
                "date": "2026-04-01",
                "category": "Maaş",
                "description": "Atomic import should rollback",
                "type": "Gelir",
                "status": "Ödendi",
                "amount": "100.0000",
                "updated_at": "not-a-date",
            }
        )
        success, message = import_database_from_json(json.dumps(payload, ensure_ascii=False))
        assert success is False
        assert "atomik" in message.lower()
        db.session.expire_all()
        assert Transaction.query.filter_by(tenant_id="default").count() == before_count


@pytest.mark.regression
@pytest.mark.security
def test_multipart_import_route_enforces_session_csrf_and_accepts_replace_mode(app, client):
    """The production-like route contract must reject missing CSRF and accept the settings token."""
    import io

    from infrastructure.database.management import export_database_to_json

    with app.app_context():
        exported = export_database_to_json(encrypt=False)

    login_response = client.post(
        "/login",
        data={"username": "emin", "password": "1"},
        follow_redirects=False,
    )
    assert login_response.status_code in {302, 303}
    settings_response = client.get("/settings")
    assert settings_response.status_code == 200
    with client.session_transaction() as session:
        csrf_token = session.get("csrf_token")
    assert csrf_token

    previous_testing = app.config.get("TESTING")
    app.config["TESTING"] = False
    try:
        missing_token = client.post(
            "/import_db_json",
            data={"db_file": (io.BytesIO(exported.encode("utf-8")), "roundtrip.json")},
            content_type="multipart/form-data",
            follow_redirects=False,
        )
        assert missing_token.status_code == 400

        valid_token = client.post(
            "/import_db_json",
            data={
                "csrf_token": csrf_token,
                "restore_mode": "replace",
                "db_file": (io.BytesIO(exported.encode("utf-8")), "roundtrip.json"),
            },
            content_type="multipart/form-data",
            follow_redirects=False,
        )
        assert valid_token.status_code in {302, 303}
        location = valid_token.headers["Location"]
        assert location.split("#")[0].rstrip("/").endswith("/settings"), location
    finally:
        app.config["TESTING"] = previous_testing



@pytest.mark.regression
def test_restore_coerces_date_datetime_and_numeric_values(app):
    from datetime import date, datetime

    from infrastructure.database.management import export_database_to_json, import_database_from_json
    from models import Transaction, User, db

    with app.app_context():
        fixture_transaction = Transaction(
            date="2026-01-01",
            category="Maaş",
            description="Type coercion fixture",
            type="Gelir",
            status="Ödendi",
            amount="100.0000",
            tenant_id="default",
        )
        db.session.add(fixture_transaction)
        db.session.commit()

        payload = json.loads(export_database_to_json(encrypt=False))
        user_row = next(row for row in payload["users"] if row["username"] == "testuser")
        transaction_row = next(
            row for row in payload["transactions"] if row["id"] == fixture_transaction.id
        )
        user_row["birthdate"] = "2000-02-11"
        user_row["last_login_at"] = "2026-08-23T08:30:00"
        transaction_row["amount"] = "1234.5600"

        success, message = import_database_from_json(json.dumps(payload, ensure_ascii=False))
        assert success, message

        db.session.expire_all()
        restored_user = db.session.get(User, user_row["id"])
        restored_transaction = db.session.get(Transaction, transaction_row["id"])
        assert restored_user.birthdate == date(2000, 2, 11)
        assert restored_user.last_login_at == datetime(2026, 8, 23, 8, 30)
        assert restored_transaction.amount == Decimal("1234.5600")


@pytest.mark.regression
def test_unknown_backup_field_fails_closed_and_rolls_back_prior_changes(app):
    from infrastructure.database.management import export_database_to_json, import_database_from_json
    from models import User, db

    with app.app_context():
        payload = json.loads(export_database_to_json(encrypt=False))
        user_row = next(row for row in payload["users"] if row["username"] == "testuser")
        user = db.session.get(User, user_row["id"])
        original_birthdate = user.birthdate
        user_row["birthdate"] = "2000-02-11"
        payload["transactions"].append(
            {
                "id": None,
                "tenant_id": "default",
                "date": "2026-04-01",
                "category": "Maaş",
                "description": "Unknown field must rollback",
                "type": "Gelir",
                "status": "Ödendi",
                "amount": "100.0000",
                "unexpected_backup_field": "reject-me",
            }
        )

        success, message = import_database_from_json(json.dumps(payload, ensure_ascii=False))
        assert success is False
        assert "schema uyumsuz" in message.lower()
        assert "unexpected_backup_field" in message

        db.session.expire_all()
        assert db.session.get(User, user_row["id"]).birthdate == original_birthdate


@pytest.mark.regression
def test_replace_mode_removes_rows_missing_from_backup_while_merge_preserves_them(app):
    from infrastructure.database.management import export_database_to_json, import_database_from_json
    from models import Transaction, db

    with app.app_context():
        payload = export_database_to_json(encrypt=False)
        extra = Transaction(
            date="2026-05-01",
            category="Maaş",
            description="Only in live database",
            type="Gelir",
            status="Ödendi",
            amount=999,
            tenant_id="default",
        )
        db.session.add(extra)
        db.session.commit()
        extra_id = extra.id

        success, message = import_database_from_json(payload, replace_existing=False)
        assert success, message
        db.session.expire_all()
        assert db.session.get(Transaction, extra_id) is not None

        success, message = import_database_from_json(payload, replace_existing=True)
        assert success, message
        db.session.expire_all()
        assert db.session.get(Transaction, extra_id) is None


@pytest.mark.regression
def test_replace_mode_flushes_parent_tenant_user_before_notification(app):
    from infrastructure.database.management import export_database_to_json, import_database_from_json
    from models import Notification, db

    with app.app_context():
        payload = json.loads(export_database_to_json(encrypt=False))
        payload["tenants"].append(
            {
                "id": "flush-test-tenant",
                "name": "Flush Test Tenant",
                "status": "active",
                "base_currency": "TRY",
            }
        )
        payload["users"].append(
            {
                "id": 991001,
                "username": "flush-test-user",
                "password": "test-password-hash",
                "role": "kullanici",
                "tenant_id": "flush-test-tenant",
                "language": "tr",
                "auth_provider": "LOCAL",
                "email_verified": False,
                "created_via": "test",
            }
        )
        payload["notifications"].append(
            {
                "id": 991001,
                "user_id": 991001,
                "tenant_id": "flush-test-tenant",
                "category": "system",
                "severity": "info",
                "priority": "normal",
                "delivery_status": "pending",
                "title": "Flush sırası testi",
                "body": "Parent kayıtlar önce materialize edilmeli.",
                "dedupe_key": "flush-test-notification",
                "is_read": False,
            }
        )

        success, message = import_database_from_json(
            json.dumps(payload, ensure_ascii=False),
            replace_existing=True,
        )
        assert success, message
        restored = Notification.query.filter_by(dedupe_key="flush-test-notification").one()
        assert restored.user_id == 991001
        assert restored.tenant_id == "flush-test-tenant"
        db.session.rollback()

