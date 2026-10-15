"""
End-to-End Integration Tests - Superadmin Access and Regular User Isolation
Verifies all 3 superadmins (emin, eminncetinn@gmail.com, eminncetinn.ai@gmail.com)
have full access to /admin/, /monitoring/, and /storage-health/,
while regular registered users have those areas completely blocked and hidden.
"""

import pytest
from models import User, Tenant, db
from werkzeug.security import generate_password_hash


@pytest.fixture
def setup_test_users(app):
    """Ensure test users exist with correct roles and credentials."""
    with app.app_context():
        # 1. Superadmin emin
        emin = User.query.filter_by(username="emin").first()
        if not emin:
            t = Tenant.query.filter_by(id="default").first() or Tenant(id="default", name="Default", status="active")
            db.session.add(t)
            emin = User(username="emin", password=generate_password_hash("1"), role="sistem_yoneticisi", tenant_id="default")
            db.session.add(emin)
        else:
            emin.password = generate_password_hash("1")
            emin.role = "sistem_yoneticisi"

        # 2. Superadmin eminncetinn@gmail.com
        u1 = User.query.filter((User.username == "eminncetinn@gmail.com") | (User.email == "eminncetinn@gmail.com")).first()
        if not u1:
            t1 = Tenant.query.filter_by(id="t_u1").first() or Tenant(id="t_u1", name="U1", status="active")
            db.session.add(t1)
            u1 = User(username="eminncetinn@gmail.com", email="eminncetinn@gmail.com", password=generate_password_hash("1"), role="sistem_yoneticisi", tenant_id="t_u1")
            db.session.add(u1)
        else:
            u1.password = generate_password_hash("1")
            u1.role = "sistem_yoneticisi"

        # 3. Superadmin eminncetinn.ai@gmail.com
        u2 = User.query.filter((User.username == "eminncetinn.ai@gmail.com") | (User.email == "eminncetinn.ai@gmail.com")).first()
        if not u2:
            t2 = Tenant.query.filter_by(id="t_u2").first() or Tenant(id="t_u2", name="U2", status="active")
            db.session.add(t2)
            u2 = User(username="eminncetinn.ai@gmail.com", email="eminncetinn.ai@gmail.com", password=generate_password_hash("1"), role="sistem_yoneticisi", tenant_id="t_u2")
            db.session.add(u2)
        else:
            u2.password = generate_password_hash("1")
            u2.role = "sistem_yoneticisi"

        # 4. Regular user (standard registered user)
        reg = User.query.filter_by(username="standard_user@example.com").first()
        if not reg:
            t_reg = Tenant.query.filter_by(id="t_reg").first() or Tenant(id="t_reg", name="Reg", status="active")
            db.session.add(t_reg)
            reg = User(username="standard_user@example.com", email="standard_user@example.com", password=generate_password_hash("password123"), role="tenant_admin", tenant_id="t_reg")
            db.session.add(reg)
        else:
            reg.role = "tenant_admin"

        db.session.commit()
        return {
            "emin_id": emin.id,
            "u1_id": u1.id,
            "u2_id": u2.id,
            "reg_id": reg.id,
        }


@pytest.mark.integration
@pytest.mark.parametrize("username,password", [
    ("emin", "1"),
    ("eminncetinn@gmail.com", "1"),
    ("eminncetinn.ai@gmail.com", "1"),
])
def test_superadmins_login_and_full_access(client, setup_test_users, username, password):
    """Verify each superadmin can authenticate and access all protected admin surfaces."""
    # 1. Login
    login_res = client.post("/login", data={"username": username, "password": password}, follow_redirects=True)
    assert login_res.status_code == 200

    # 2. Access Admin Panel
    admin_res = client.get("/admin/", follow_redirects=False)
    assert admin_res.status_code == 200, f"{username} /admin/ erişemedi: {admin_res.status_code}"

    # 3. Access Monitoring
    mon_res = client.get("/monitoring/", follow_redirects=False)
    assert mon_res.status_code == 200, f"{username} /monitoring/ erişemedi: {mon_res.status_code}"

    # 4. Access Storage Health
    sh_res = client.get("/storage-health/", follow_redirects=False)
    assert sh_res.status_code == 200, f"{username} /storage-health/ erişemedi: {sh_res.status_code}"

    # 5. Check Settings page has storage health and db tuneup
    settings_res = client.get("/settings", follow_redirects=True)
    settings_html = settings_res.get_data(as_text=True)
    assert "/storage-health/" in settings_html
    assert "Veritabanını Şimdi Optimize Et" in settings_html

    # 6. Check Sidebar contains admin link
    assert "/admin/" in settings_html
    assert "/monitoring/" in settings_html


@pytest.mark.integration
def test_regular_user_blocked_and_isolated(client, setup_test_users):
    """Verify a regular registered user is blocked from admin routes and sees clean UI without admin items."""
    # 1. Login as standard user
    login_res = client.post("/login", data={"username": "standard_user@example.com", "password": "password123"}, follow_redirects=True)
    assert login_res.status_code == 200

    # 2. Blocked from /admin/
    admin_res = client.get("/admin/", follow_redirects=False)
    assert admin_res.status_code in [302, 403]
    if admin_res.status_code == 302:
        assert "/admin" not in admin_res.headers.get("Location", "")

    # 3. Blocked from /monitoring/
    mon_res = client.get("/monitoring/", follow_redirects=False)
    assert mon_res.status_code in [302, 403]
    if mon_res.status_code == 302:
        assert "/monitoring" not in mon_res.headers.get("Location", "")

    # 4. Blocked from /storage-health/
    sh_res = client.get("/storage-health/", follow_redirects=False)
    assert sh_res.status_code in [302, 403]
    if sh_res.status_code == 302:
        assert "/storage-health" not in sh_res.headers.get("Location", "")

    # 5. UI: Settings page must NOT contain storage health link or db tuneup card
    settings_res = client.get("/settings", follow_redirects=True)
    settings_html = settings_res.get_data(as_text=True)
    assert "Veritabanını Şimdi Optimize Et" not in settings_html
    assert 'href="/storage-health/"' not in settings_html
    assert "url_for('storage_health" not in settings_html

    # 6. UI: Categories and Profile must NOT contain storage health link
    cat_res = client.get("/categories", follow_redirects=True)
    assert "Depolama Sağlığı &amp; Bakım" not in cat_res.get_data(as_text=True)

    prof_res = client.get("/profile", follow_redirects=True)
    assert "Depolama Sağlığı &amp; Bakım" not in prof_res.get_data(as_text=True)

    # 7. Sidebar must NOT contain admin or monitoring links
    assert 'href="/admin/"' not in settings_html
    assert 'href="/monitoring/"' not in settings_html
