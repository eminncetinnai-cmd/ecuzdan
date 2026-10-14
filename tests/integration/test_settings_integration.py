"""Integration tests for authentication boundaries of the Settings API."""

import pytest


@pytest.mark.integration
class TestSettingsAPIIntegration:
    """Unauthenticated settings requests must never reach mutation services."""

    @staticmethod
    def _assert_login_redirect(response):
        assert response.status_code == 302
        assert '/login' in response.headers.get('Location', '')

    @pytest.fixture
    def client(self, app):
        """Use the shared isolated Flask test client."""
        return app.test_client()

    def test_settings_index_requires_auth(self, client):
        self._assert_login_redirect(client.get('/settings'))

    def test_settings_logout_other_devices_requires_auth(self, client):
        self._assert_login_redirect(client.post('/logout_other_devices'))

    def test_settings_toggle_privacy_mode_requires_auth(self, client):
        self._assert_login_redirect(client.post('/toggle_privacy_mode'))

    def test_settings_reset_data_requires_auth(self, client):
        self._assert_login_redirect(client.post('/reset_data'))

    def test_settings_change_password_requires_auth(self, client):
        self._assert_login_redirect(client.post('/settings', data={'action': 'change_pw'}))

    def test_settings_change_currency_requires_auth(self, client):
        self._assert_login_redirect(client.post('/settings', data={'action': 'change_base_currency'}))

    def test_settings_change_theme_requires_auth(self, client):
        self._assert_login_redirect(client.post('/settings', data={'action': 'change_theme'}))

    def test_settings_set_privacy_mode_requires_auth(self, client):
        self._assert_login_redirect(client.post('/settings', data={'action': 'set_privacy_mode'}))

    def test_settings_change_language_requires_auth(self, client):
        self._assert_login_redirect(client.post('/settings', data={'action': 'change_language'}))

    def test_settings_update_profile_requires_auth(self, client):
        self._assert_login_redirect(client.post('/settings', data={'action': 'update_profile'}))

    def test_settings_blueprint_registered(self, app, client):
        assert any(rule.rule == '/settings' for rule in app.url_map.iter_rules())
        assert client.get('/settings').status_code == 302

    def test_settings_post_with_invalid_action_requires_auth(self, client):
        self._assert_login_redirect(client.post('/settings', data={'action': 'invalid'}))


    def test_settings_set_language_persists_user_and_session(self, authenticated_client, test_user):
        response = authenticated_client.post('/set_language/en')

        assert response.status_code == 200
        payload = response.get_json()
        assert payload['language'] == 'en'
        assert payload['status'] == 'success'
        assert payload['success'] is True
        assert payload['message'] == 'Language updated successfully.'
        from models import User, db
        db.session.expire_all()
        persisted_user = db.session.get(User, test_user.id)
        assert persisted_user.language == 'en'
        with authenticated_client.session_transaction() as session:
            assert session['lang'] == 'en'
            assert session['lang_source'] == 'explicit'

    def test_settings_language_preference_survives_fresh_login(self, app, test_user):
        from models import db

        test_user.language = 'tr'
        db.session.commit()
        client = app.test_client()
        response = client.post('/login', data={'username': 'testuser', 'password': 'testpass'})

        assert response.status_code == 302
        with client.session_transaction() as session:
            assert session['lang'] == 'tr'
            assert session['lang_source'] == 'user'

        with app.test_request_context('/'):
            from flask import session
            session['user_id'] = test_user.id
            session['lang'] = 'it'
            session['lang_source'] = 'user'
            assert app.extensions['e_cuzdan_i18n'].get_locale() == 'tr'

    def test_settings_set_language_rejects_unsupported_language(self, authenticated_client, test_user):
        response = authenticated_client.post('/set_language/xx')

        assert response.status_code == 400
        payload = response.get_json()
        assert payload['success'] is False
        assert payload['status'] == 'error'
        from models import db
        db.session.expire_all()
        assert db.session.get(type(test_user), test_user.id).language == 'tr'

    def test_settings_set_language_requires_post(self, authenticated_client):
        response = authenticated_client.get('/set_language/en')
        assert response.status_code == 405

    def test_settings_change_password_requires_current_password(self, authenticated_client, test_user):
        from models import User, db
        from werkzeug.security import check_password_hash

        response = authenticated_client.post('/settings', data={
            'action': 'change_pw',
            'new_pw': 'NewValidPassword123!',
            'csrf_token': authenticated_client.get('/settings').data  # not strictly validated in tests or session
        }, follow_redirects=True)

        assert response.status_code == 200
        db.session.expire_all()
        user = db.session.get(User, test_user.id)
        assert check_password_hash(user.password, 'testpass')
        assert not check_password_hash(user.password, 'NewValidPassword123!')

    def test_settings_change_password_rejects_wrong_current_password(self, authenticated_client, test_user):
        from models import User, db
        from werkzeug.security import check_password_hash

        response = authenticated_client.post('/settings', data={
            'action': 'change_pw',
            'current_pw': 'WrongPassword999',
            'new_pw': 'NewValidPassword123!',
        }, follow_redirects=True)

        assert response.status_code == 200
        db.session.expire_all()
        user = db.session.get(User, test_user.id)
        assert check_password_hash(user.password, 'testpass')
        assert not check_password_hash(user.password, 'NewValidPassword123!')

    def test_settings_change_password_succeeds_with_correct_current_password(self, authenticated_client, test_user):
        from models import User, db
        from werkzeug.security import check_password_hash

        response = authenticated_client.post('/settings', data={
            'action': 'change_pw',
            'current_pw': 'testpass',
            'new_pw': 'NewValidPassword123!',
        }, follow_redirects=True)

        assert response.status_code == 200
        db.session.expire_all()
        user = db.session.get(User, test_user.id)
        assert check_password_hash(user.password, 'NewValidPassword123!')
        assert not check_password_hash(user.password, 'testpass')

