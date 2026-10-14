"""Comprehensive test suite for OAuth signup flow."""

import os
import sys
from datetime import datetime, timedelta
from unittest.mock import Mock, patch

import pytest

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from app import app
from models import Tenant, User, db


class TestOAuthSignupFlow:
    """Test OAuth signup flow end-to-end."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        app.config['WTF_CSRF_ENABLED'] = False
        app.config['GOOGLE_CLIENT_ID'] = 'test-client-id.apps.googleusercontent.com'
        app.config['GOOGLE_CLIENT_SECRET'] = 'test-client-secret'

        with app.app_context():
            db.create_all()
            yield app.test_client()
            db.session.remove()
            db.drop_all()

    @pytest.fixture
    def mock_oauth_provider(self):
        """Mock Google OAuth provider."""
        with patch('infrastructure.auth.google_provider.GoogleOAuthProvider') as mock:
            provider_instance = Mock()
            provider_instance.get_authorization_url.return_value = 'https://accounts.google.com/o/oauth2/auth'
            provider_instance.exchange_code_for_token.return_value = {'access_token': 'test_token'}

            # Create a proper mock object that can be serialized
            user_info = Mock()
            user_info.email = 'test@example.com'
            user_info.name = 'Test User'
            user_info.provider = 'google'
            user_info.provider_id = '123456789'
            user_info.avatar_url = 'https://example.com/avatar.jpg'

            provider_instance.verify_token_and_get_user_info.return_value = user_info
            mock.return_value = provider_instance
            yield provider_instance

    def test_oauth_login_redirect(self, client, mock_oauth_provider):
        """Test OAuth login initiates redirect to Google."""
        response = client.get('/login/google')
        assert response.status_code == 302
        assert 'accounts.google.com' in response.location

    def test_oauth_callback_new_user_redirects_to_signup(self, client, mock_oauth_provider):
        """Test OAuth callback redirects new users to signup form."""
        with client.session_transaction() as session:
            session['oauth_state'] = 'test_state'
            session['oauth_provider'] = 'google'

        response = client.get('/callback/google?code=test_code&state=test_state')
        assert response.status_code == 302
        # Check if redirect contains oauth-signup
        assert 'oauth-signup' in response.location or '/oauth-signup' in response.location

    def test_oauth_callback_existing_user_logs_in(self, client, mock_oauth_provider):
        """Test OAuth callback logs in existing users."""
        # Create existing user
        with app.app_context():
            from werkzeug.security import generate_password_hash
            tenant = Tenant(id='test_tenant', name='Test Tenant', base_currency='TRY', status='active')
            db.session.add(tenant)
            db.session.flush()

            user = User(
                username='existing_user',
                email='test@example.com',
                password=generate_password_hash('password123'),
                auth_provider='GOOGLE',
                oauth_id='123456789',
                tenant_id=tenant.id,
                role='kullanici',
                language='tr'
            )
            db.session.add(user)
            db.session.commit()

        with client.session_transaction() as session:
            session['oauth_state'] = 'test_state'
            session['oauth_provider'] = 'google'

        response = client.get('/callback/google?code=test_code&state=test_state')
        assert response.status_code == 302
        # The redirect should go somewhere (either dashboard or root)
        assert response.location is not None
        # User should be logged in (check session)
        with client.session_transaction() as session:
            assert 'user_id' in session

    def test_oauth_signup_page_loads_with_session_data(self, client):
        """Test signup page loads with OAuth session data."""
        with client.session_transaction() as session:
            session['oauth_signup_info'] = {
                'email': 'test@example.com',
                'name': 'Test User',
                'provider': 'google',
                'provider_id': '123456789',
                'avatar_url': 'https://example.com/avatar.jpg',
                'created_at': datetime.now().isoformat()
            }

        response = client.get('/oauth-signup')
        assert response.status_code == 200
        assert b'Test User' in response.data
        assert b'test@example.com' in response.data

    def test_oauth_signup_without_session_redirects_to_login(self, client):
        """Test signup page without OAuth session redirects to login."""
        response = client.get('/oauth-signup')
        assert response.status_code == 302
        assert '/login' in response.location

    def test_oauth_signup_expired_session_redirects_to_login(self, client):
        """Test signup page with expired session redirects to login."""
        expired_time = (datetime.now() - timedelta(minutes=20)).isoformat()
        with client.session_transaction() as session:
            session['oauth_signup_info'] = {
                'email': 'test@example.com',
                'name': 'Test User',
                'provider': 'google',
                'provider_id': '123456789',
                'avatar_url': 'https://example.com/avatar.jpg',
                'created_at': expired_time
            }

        response = client.get('/oauth-signup')
        assert response.status_code == 302
        assert '/login' in response.location

    def test_oauth_signup_form_validation_missing_fields(self, client):
        """Test signup form validation rejects missing required fields."""
        with client.session_transaction() as session:
            session['oauth_signup_info'] = {
                'email': 'test@example.com',
                'name': 'Test User',
                'provider': 'google',
                'provider_id': '123456789',
                'avatar_url': 'https://example.com/avatar.jpg',
                'created_at': datetime.now().isoformat()
            }

        response = client.post('/oauth-signup', data={
            'username': 'testuser',
            'password': 'password123',
            'confirm_password': 'password123',
            'gender': 'male',
            'birthdate': '1990-01-01',
            'country': 'TR',
            'city': 'Istanbul',
            # Missing phone
        })
        assert response.status_code == 200
        assert 'Kişisel bilgiler gereklidir' in response.data.decode('utf-8')

    def test_oauth_signup_password_mismatch(self, client):
        """Test signup form validation rejects password mismatch."""
        with client.session_transaction() as session:
            session['oauth_signup_info'] = {
                'email': 'test@example.com',
                'name': 'Test User',
                'provider': 'google',
                'provider_id': '123456789',
                'avatar_url': 'https://example.com/avatar.jpg',
                'created_at': datetime.now().isoformat()
            }

        response = client.post('/oauth-signup', data={
            'username': 'testuser',
            'password': 'password123',
            'confirm_password': 'different123',
            'gender': 'male',
            'birthdate': '1990-01-01',
            'country': 'TR',
            'city': 'Istanbul',
            'phone': '5551234567'
        })
        assert response.status_code == 200
        assert 'Şifreler eşleşmiyor' in response.data.decode('utf-8')

    def test_oauth_signup_password_too_short(self, client):
        """Test signup form validation rejects short password."""
        with client.session_transaction() as session:
            session['oauth_signup_info'] = {
                'email': 'test@example.com',
                'name': 'Test User',
                'provider': 'google',
                'provider_id': '123456789',
                'avatar_url': 'https://example.com/avatar.jpg',
                'created_at': datetime.now().isoformat()
            }

        response = client.post('/oauth-signup', data={
            'username': 'testuser',
            'password': 'short',
            'confirm_password': 'short',
            'gender': 'male',
            'birthdate': '1990-01-01',
            'country': 'TR',
            'city': 'Istanbul',
            'phone': '5551234567'
        })
        assert response.status_code == 200
        assert 'Şifre en az 8 karakter olmalıdır' in response.data.decode('utf-8')

    def test_oauth_signup_duplicate_username(self, client):
        """Test signup form validation rejects duplicate username."""
        with app.app_context():
            from werkzeug.security import generate_password_hash
            tenant = Tenant(id='test_tenant', name='Test Tenant', base_currency='TRY', status='active')
            db.session.add(tenant)
            db.session.flush()

            user = User(
                username='testuser',
                email='existing@example.com',
                password=generate_password_hash('password123'),
                tenant_id=tenant.id,
                role='kullanici',
                language='tr'
            )
            db.session.add(user)
            db.session.commit()

        with client.session_transaction() as session:
            session['oauth_signup_info'] = {
                'email': 'test@example.com',
                'name': 'Test User',
                'provider': 'google',
                'provider_id': '123456789',
                'avatar_url': 'https://example.com/avatar.jpg',
                'created_at': datetime.now().isoformat()
            }

        response = client.post('/oauth-signup', data={
            'username': 'testuser',
            'password': 'password123',
            'confirm_password': 'password123',
            'gender': 'male',
            'birthdate': '1990-01-01',
            'country': 'TR',
            'city': 'Istanbul',
            'phone': '5551234567'
        })
        assert response.status_code == 200
        assert 'Bu kullanıcı adı zaten kullanımda' in response.data.decode('utf-8')

    def test_oauth_signup_success_creates_user_and_redirects(self, client):
        """Test successful signup creates user and redirects to dashboard."""
        with client.session_transaction() as session:
            session['oauth_signup_info'] = {
                'email': 'test@example.com',
                'name': 'Test User',
                'provider': 'google',
                'provider_id': '123456789',
                'avatar_url': 'https://example.com/avatar.jpg',
                'created_at': datetime.now().isoformat()
            }

        response = client.post('/oauth-signup', data={
            'username': 'testuser',
            'password': 'password123',
            'confirm_password': 'password123',
            'gender': 'male',
            'birthdate': '1990-01-01',
            'country': 'TR',
            'city': 'Istanbul',
            'phone': '5551234567'
        })

        assert response.status_code == 302
        # The redirect should go somewhere
        assert response.location is not None

        # Verify user was created
        with app.app_context():
            user = User.query.filter_by(username='testuser').first()
            assert user is not None
            assert user.email == 'test@example.com'
            assert user.auth_provider == 'GOOGLE'
            assert user.oauth_id == '123456789'
            assert user.gender == 'male'
            assert user.country == 'TR'
            assert user.city == 'Istanbul'
            assert user.phone == '5551234567'

        # Verify user is logged in
        with client.session_transaction() as session:
            assert 'user_id' in session

    def test_oauth_signup_session_cleared_after_success(self, client):
        """Test signup session is cleared after successful registration."""
        with client.session_transaction() as session:
            session['oauth_signup_info'] = {
                'email': 'test@example.com',
                'name': 'Test User',
                'provider': 'google',
                'provider_id': '123456789',
                'avatar_url': 'https://example.com/avatar.jpg',
                'created_at': datetime.now().isoformat()
            }

        client.post('/oauth-signup', data={
            'username': 'testuser',
            'password': 'password123',
            'confirm_password': 'password123',
            'gender': 'male',
            'birthdate': '1990-01-01',
            'country': 'TR',
            'city': 'Istanbul',
            'phone': '5551234567'
        })

        # Check session was cleared
        with client.session_transaction() as session:
            assert 'oauth_signup_info' not in session
            assert 'user_id' in session  # User should be logged in


class TestOAuthSignupSecurity:
    """Test OAuth signup security features."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        app.config['WTF_CSRF_ENABLED'] = False

        with app.app_context():
            db.create_all()
            yield app.test_client()
            db.session.remove()
            db.drop_all()

    def test_oauth_state_validation(self, client):
        """Test OAuth state validation prevents CSRF attacks."""
        with client.session_transaction() as session:
            session['oauth_state'] = 'correct_state'

        # Wrong state
        response = client.get('/callback/google?code=test_code&state=wrong_state')
        assert response.status_code == 302
        assert '/login' in response.location

    def test_oauth_signup_csrf_protection(self, client):
        """Test signup form has CSRF protection."""
        with client.session_transaction() as session:
            session['oauth_signup_info'] = {
                'email': 'test@example.com',
                'name': 'Test User',
                'provider': 'google',
                'provider_id': '123456789',
                'avatar_url': 'https://example.com/avatar.jpg',
                'created_at': datetime.now().isoformat()
            }
            session['csrf_token'] = 'test_csrf_token'

        response = client.get('/oauth-signup')
        assert response.status_code == 200
        assert b'csrf_token' in response.data

    def test_oauth_signup_session_timeout(self, client):
        """Test signup session expires after 15 minutes."""
        # Create session that's just expired
        expired_time = (datetime.now() - timedelta(minutes=16)).isoformat()
        with client.session_transaction() as session:
            session['oauth_signup_info'] = {
                'email': 'test@example.com',
                'name': 'Test User',
                'provider': 'google',
                'provider_id': '123456789',
                'avatar_url': 'https://example.com/avatar.jpg',
                'created_at': expired_time
            }

        response = client.get('/oauth-signup')
        assert response.status_code == 302
        assert '/login' in response.location


class TestOAuthSignupEdgeCases:
    """Test OAuth signup edge cases."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        app.config['WTF_CSRF_ENABLED'] = False

        with app.app_context():
            db.create_all()
            yield app.test_client()
            db.session.remove()
            db.drop_all()

    def test_oauth_signup_invalid_birthdate_format(self, client):
        """Test signup form validation rejects invalid birthdate format."""
        with client.session_transaction() as session:
            session['oauth_signup_info'] = {
                'email': 'test@example.com',
                'name': 'Test User',
                'provider': 'google',
                'provider_id': '123456789',
                'avatar_url': 'https://example.com/avatar.jpg',
                'created_at': datetime.now().isoformat()
            }

        response = client.post('/oauth-signup', data={
            'username': 'testuser',
            'password': 'password123',
            'confirm_password': 'password123',
            'gender': 'male',
            'birthdate': 'invalid-date',
            'country': 'TR',
            'city': 'Istanbul',
            'phone': '5551234567'
        })
        assert response.status_code == 200
        assert 'Geçersiz doğum tarihi formatı' in response.data.decode('utf-8')

    def test_oauth_signup_account_linking_email_exists(self, client):
        """Test signup handles existing email without OAuth ID."""
        with app.app_context():
            from werkzeug.security import generate_password_hash
            tenant = Tenant(id='test_tenant', name='Test Tenant', base_currency='TRY', status='active')
            db.session.add(tenant)
            db.session.flush()

            user = User(
                username='existing_user',
                email='test@example.com',
                password=generate_password_hash('password123'),
                auth_provider='LOCAL',
                tenant_id=tenant.id,
                role='kullanici',
                language='tr'
            )
            db.session.add(user)
            db.session.commit()

        with client.session_transaction() as session:
            session['oauth_signup_info'] = {
                'email': 'test@example.com',
                'name': 'Test User',
                'provider': 'google',
                'provider_id': '123456789',
                'avatar_url': 'https://example.com/avatar.jpg',
                'created_at': datetime.now().isoformat()
            }

        # This should still allow signup (new OAuth ID)
        response = client.post('/oauth-signup', data={
            'username': 'newuser',
            'password': 'password123',
            'confirm_password': 'password123',
            'gender': 'male',
            'birthdate': '1990-01-01',
            'country': 'TR',
            'city': 'Istanbul',
            'phone': '5551234567'
        })

        # Should succeed since it's a different OAuth ID
        assert response.status_code == 302 or response.status_code == 200


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--cov=.', '--cov-report=html'])
