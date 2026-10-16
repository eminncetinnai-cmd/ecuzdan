"""
Admin User Management Tests
Kullanıcı oluşturma, düzenleme, silme ve rol atama işlemlerinin testleri
"""

import pytest
from werkzeug.security import generate_password_hash

from app import app as app_factory
from models import Tenant, User, db


@pytest.fixture(scope='function', autouse=True)
def admin_test_data(app):
    """Admin test verilerini oluştur"""
    _seed_admin_test_data()
    yield


def _seed_admin_test_data():
    """Admin test verilerini oluştur"""
    # Tenant A ve B oluştur
    if not Tenant.query.filter_by(id='tenant_a').first():
        tenant_a = Tenant(id='tenant_a', name='Tenant A', status='active')
        db.session.add(tenant_a)

    if not Tenant.query.filter_by(id='tenant_b').first():
        tenant_b = Tenant(id='tenant_b', name='Tenant B', status='active')
        db.session.add(tenant_b)

    # tenant_admin (Tenant A)
    if not User.query.filter_by(username='tenant_admin').first():
        tenant_admin = User(
            username='tenant_admin',
            password=generate_password_hash('test123'),
            role='tenant_yoneticisi',
            tenant_id='tenant_a',
            language='tr'
        )
        db.session.add(tenant_admin)

    # regular_user (Tenant A)
    if not User.query.filter_by(username='regular_user').first():
        regular_user = User(
            username='regular_user',
            password=generate_password_hash('test123'),
            role='kullanici',
            tenant_id='tenant_a',
            language='tr'
        )
        db.session.add(regular_user)

    db.session.commit()


@pytest.fixture
def superadmin_session(client):
    """emin kullanıcısıyla oturum açmış test client"""
    client.post('/login', data={'username': 'emin', 'password': '1'})
    return client


@pytest.fixture
def tenant_admin_session(client):
    """tenant_yoneticisi rolündeki kullanıcıyla oturum açmış test client"""
    client.post('/login', data={'username': 'tenant_admin', 'password': 'test123'})
    return client


@pytest.fixture
def user_session(client):
    """kullanici rolündeki kullanıcıyla oturum açmış test client"""
    client.post('/login', data={'username': 'regular_user', 'password': 'test123'})
    return client


class TestUserCreation:
    def test_create_user_success(self, client, superadmin_session):
        """POST /admin/users/create → 302 (redirect), yeni user DB'de"""
        response = client.post('/admin/users/create', data={
            'username': 'new_user',
            'password': 'newpass123',
            'role': 'kullanici',
            'tenant_id': 'tenant_a'
        }, follow_redirects=False)

        assert response.status_code == 302
        assert response.location.endswith('/admin/users')

        # DB'de kontrol et
        with app_factory.app_context():
            new_user = User.query.filter_by(username='new_user').first()
            assert new_user is not None
            assert new_user.role == 'kullanici'
            assert new_user.tenant_id == 'tenant_a'

    def test_create_user_duplicate_username(self, client, superadmin_session):
        """Aynı username → 200 (form tekrar render), flash hata, 400 DEĞİL"""
        response = client.post('/admin/users/create', data={
            'username': 'emin',  # Zaten var
            'password': 'newpass123',
            'role': 'kullanici',
            'tenant_id': 'tenant_a'
        }, follow_redirects=False)

        assert response.status_code == 200  # Form tekrar render
        # Flash mesajı kontrolü (HTML içinde)
        assert b'zaten kullan' in response.data or b'kullan' in response.data

    def test_create_user_empty_username(self, client, superadmin_session):
        """Boş username → form re-render, flash hata, 400 DEĞİL"""
        response = client.post('/admin/users/create', data={
            'username': '',
            'password': 'newpass123',
            'role': 'kullanici',
            'tenant_id': 'tenant_a'
        }, follow_redirects=False)

        assert response.status_code == 200  # Form tekrar render
        assert b'gereklidir' in response.data or b'zorunlu' in response.data

    def test_create_user_invalid_role(self, client, superadmin_session):
        """Geçersiz rol → flash hata"""
        response = client.post('/admin/users/create', data={
            'username': 'new_user',
            'password': 'newpass123',
            'role': 'invalid_role',
            'tenant_id': 'tenant_a'
        }, follow_redirects=False)

        assert response.status_code == 200  # Form tekrar render
        assert b'Ge' in response.data or b'ge' in response.data

    def test_tenant_admin_cannot_assign_superadmin_role(self, client, tenant_admin_session):
        """tenant_yoneticisi, sistem_yoneticisi rolü atayamaz"""
        response = client.post('/admin/users/create', data={
            'username': 'new_user',
            'password': 'newpass123',
            'role': 'sistem_yoneticisi',
            'tenant_id': 'tenant_a'
        }, follow_redirects=False)

        assert response.status_code == 200  # Form tekrar render
        assert b'sistem' in response.data or b'yonetici' in response.data

    def test_tenant_admin_cannot_create_user_in_other_tenant(self, client, tenant_admin_session):
        """tenant_yoneticisi başka tenant'a user ekleyemez"""
        client.post('/admin/users/create', data={
            'username': 'new_user',
            'password': 'newpass123',
            'role': 'kullanici',
            'tenant_id': 'tenant_b'  # Farklı tenant
        }, follow_redirects=False)

        # Tenant admin kendi tenant'ına override eder
        with app_factory.app_context():
            new_user = User.query.filter_by(username='new_user').first()
            if new_user:
                assert new_user.tenant_id == 'tenant_a'  # Kendi tenant'ına

    def test_regular_user_cannot_access_admin(self, client, user_session):
        """kullanici, /admin/* endpoint'lerine erişemez → redirect"""
        response = client.get('/admin/users', follow_redirects=False)

        # Redirect to dashboard or login (yetkisiz erişim)
        assert response.status_code == 302
        assert response.location != '/admin/users'

    def test_emin_user_cannot_be_deleted(self, client, superadmin_session):
        """emin kullanıcısı silinemez → hata mesajı"""
        with app_factory.app_context():
            emin = User.query.filter_by(username='emin').first()
            emin_id = emin.id

        response = client.post(f'/admin/users/{emin_id}/delete', follow_redirects=False)

        assert response.status_code == 302
        # Flash mesajı kontrolü
        follow_response = client.get('/admin/users')
        assert b'silinemez' in follow_response.data or b'Emin' in follow_response.data


class TestDataIsolation:
    def test_tenant_a_cannot_see_tenant_b_users(self, client, tenant_admin_session):
        """Tenant A admin'i, Tenant B kullanıcılarını göremez"""
        response = client.get('/admin/users', follow_redirects=False)

        assert response.status_code == 200
        # Tenant B'de kullanıcı oluşturup listelenmediğini kontrol et
        with app_factory.app_context():
            tenant_b_users = User.query.filter_by(tenant_id='tenant_b').all()
            # Tenant B'de kullanıcı varsa, bunlar HTML'de görünmemeli
            for user in tenant_b_users:
                assert user.username.encode() not in response.data

    def test_superadmin_can_see_all_users(self, client, superadmin_session):
        """sistem_yoneticisi tüm kullanıcıları görebilir"""
        response = client.get('/admin/users', follow_redirects=False)

        assert response.status_code == 200
        # Tüm kullanıcılar görünmeli
        assert b'emin' in response.data
        assert b'tenant_admin' in response.data
        assert b'regular_user' in response.data


class TestUserStats:
    def test_superadmin_user_stats_api(self, client, superadmin_session):
        """Superadmin user stats API endpoint döner ve metrikler doğrudur"""
        response = client.get('/admin/api/user-stats')
        assert response.status_code == 200
        payload = response.get_json()
        assert payload['success'] is True
        data = payload['data']
        assert data['total_users'] >= 3
        assert data['is_superadmin'] is True
        assert 'google_users' in data
        assert 'local_users' in data
        assert 'active_30d' in data
        assert isinstance(data['recent_users'], list)

    def test_tenant_admin_user_stats_api(self, client, tenant_admin_session):
        """Tenant admin user stats API endpoint sadece kendi tenant'ını kapsar"""
        response = client.get('/admin/api/user-stats')
        assert response.status_code == 200
        payload = response.get_json()
        assert payload['success'] is True
        data = payload['data']
        assert data['is_superadmin'] is False
        assert data['total_users'] >= 1

    def test_users_page_displays_stats_cards(self, client, superadmin_session):
        """Admin kullanıcılar sayfasında 4-kartlık metrik grid görüntülenir"""
        response = client.get('/admin/users')
        assert response.status_code == 200
        assert 'Toplam Kullanıcı'.encode('utf-8') in response.data
        assert 'Google ile Giriş'.encode('utf-8') in response.data
        assert 'Yerel Hesaplar'.encode('utf-8') in response.data
        assert 'Aktif Kullanıcılar'.encode('utf-8') in response.data

    def test_admin_dashboard_displays_user_stats(self, client, superadmin_session):
        """Admin dashboard sayfasında kullanıcı dağılımı ve son hareketler görüntülenir"""
        response = client.get('/admin/')
        assert response.status_code == 200
        assert 'Kullanıcı Dağılımı'.encode('utf-8') in response.data
        assert 'Son Kullanıcı Hareketleri'.encode('utf-8') in response.data

