"""
tests/unit/test_admin_audit_routes.py
=====================================
Unit tests for Admin Live Audit & Cryptographic Integrity Dashboard.
"""

from werkzeug.security import generate_password_hash

from models import AuditLog, User, db


def test_admin_audit_dashboard_superadmin(app, client):
    """Superadmin can access the live audit dashboard and view all integrity metrics."""
    with app.app_context():
        # Ensure superadmin user exists
        admin = User.query.filter_by(username="emin").first()
        if not admin:
            admin = User(
                username="emin",
                password=generate_password_hash("1"),
                role="sistem_yoneticisi",
                tenant_id="default",
            )
            db.session.add(admin)
            db.session.commit()

    # Login as superadmin
    res = client.post("/login", data={"username": "emin", "password": "1"}, follow_redirects=True)
    assert res.status_code == 200

    # Access audit dashboard
    res = client.get("/admin/audit")
    assert res.status_code == 200
    html = res.get_data(as_text=True)

    assert "Canlı Denetim &amp; Kriptografik Bütünlük" in html
    assert "Defter Bekçisi Durumu" in html
    assert "SHA-256 Kripto Zincir" in html
    assert "SAĞLIKLI" in html


def test_admin_audit_run_watchdog_scan(app, client):
    """POST /admin/audit/run-watchdog executes an on-demand scan and logs audit event."""
    with app.app_context():
        admin = User.query.filter_by(username="emin").first()
        if not admin:
            admin = User(
                username="emin",
                password=generate_password_hash("1"),
                role="sistem_yoneticisi",
                tenant_id="default",
            )
            db.session.add(admin)
            db.session.commit()

    client.post("/login", data={"username": "emin", "password": "1"}, follow_redirects=True)

    res = client.post("/admin/audit/run-watchdog", follow_redirects=True)
    assert res.status_code == 200
    html = res.get_data(as_text=True)
    assert "Bütünlük Taraması Başarılı" in html

    # Verify audit event in DB
    with app.app_context():
        latest_audit = AuditLog.query.filter_by(action="LEDGER_AUDIT_ON_DEMAND").order_by(AuditLog.id.desc()).first()
        assert latest_audit is not None
        assert latest_audit.username == "emin"


def test_admin_audit_unauthorized_user(app, client):
    """Standard user without admin role cannot access /admin/audit."""
    with app.app_context():
        user = User.query.filter_by(username="testuser").first()
        if not user:
            user = User(
                username="testuser",
                password=generate_password_hash("testpass"),
                role="kullanici",
                tenant_id="default",
            )
            db.session.add(user)
            db.session.commit()

    client.post("/login", data={"username": "testuser", "password": "testpass"}, follow_redirects=True)
    res = client.get("/admin/audit")
    # Should be redirected or 403 Forbidden
    assert res.status_code in (302, 403)


def test_admin_audit_unauthenticated(app, client):
    """Anonymous client cannot access /admin/audit."""
    res = client.get("/admin/audit")
    assert res.status_code == 302
    assert "/login" in res.headers.get("Location", "")
