"""
Unit Tests - Auth Helpers
Authentication and authorization utility functions
"""

from unittest.mock import Mock, patch

import pytest
from flask import Flask, g, session

from utils.auth_helpers import (
    get_current_user,
    login_required,
    normalize_role,
    require_role,
    set_tenant_context,
    superadmin_required,
    tenant_admin_required,
)


@pytest.mark.unit
def test_login_required_decorator_with_user():
    """Test login_required decorator with authenticated user"""
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'test'

    @login_required
    def protected_view():
        return 'Protected content'

    with app.test_request_context():
        session['user_id'] = '123'
        result = protected_view()
        assert result == 'Protected content'


@pytest.mark.unit
def test_login_required_decorator_without_user():
    """Test login_required decorator without authenticated user"""
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'test'

    @login_required
    def protected_view():
        return 'Protected content'

    with app.test_request_context():
        with patch('utils.auth_helpers.url_for'):
            with patch('utils.auth_helpers.redirect') as mock_redirect:
                mock_redirect.return_value = Mock(status_code=302)
                protected_view()
                assert mock_redirect.called


@pytest.mark.unit
def test_require_role_decorator_with_valid_role():
    """Test require_role decorator with valid role"""
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'test'

    @require_role('yonetici')
    def protected_view():
        return 'Protected content'

    with app.test_request_context():
        session['user_id'] = '123'
        with patch('utils.auth_helpers.db.session.get') as mock_get:
            mock_user = Mock()
            mock_user.role = 'yonetici'
            mock_get.return_value = mock_user
            result = protected_view()
            assert result == 'Protected content'


@pytest.mark.unit
def test_require_role_decorator_without_user():
    """Test require_role decorator without user"""
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'test'

    @require_role('yonetici')
    def protected_view():
        return 'Protected content'

    with app.test_request_context():
        with patch('utils.auth_helpers.url_for'):
            with patch('utils.auth_helpers.redirect') as mock_redirect:
                mock_redirect.return_value = Mock(status_code=302)
                protected_view()
                assert mock_redirect.called


@pytest.mark.unit
def test_require_role_decorator_with_invalid_role():
    """Test require_role decorator with invalid role"""
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'test'

    @require_role('yonetici')
    def protected_view():
        return 'Protected content'

    with app.test_request_context():
        session['user_id'] = '123'
        with patch('utils.auth_helpers.db.session.get') as mock_get:
            mock_user = Mock(
                role='kullanici',
                is_super_admin=False,
                special_code=None,
                special_code_used_at=None,
            )
            mock_get.return_value = mock_user
            with patch('utils.auth_helpers.url_for'):
                with patch('utils.auth_helpers.redirect') as mock_redirect:
                    mock_redirect.return_value = Mock(status_code=302)
                    protected_view()
                    assert mock_redirect.called


@pytest.mark.unit
def test_require_role_decorator_user_not_found():
    """Test require_role decorator when user not found"""
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'test'

    @require_role('yonetici')
    def protected_view():
        return 'Protected content'

    with app.test_request_context():
        session['user_id'] = '123'
        with patch('utils.auth_helpers.db.session.get') as mock_get:
            mock_get.return_value = None
            with patch('utils.auth_helpers.url_for'):
                with patch('utils.auth_helpers.redirect') as mock_redirect:
                    mock_redirect.return_value = Mock(status_code=302)
                    protected_view()
                    assert mock_redirect.called


@pytest.mark.unit
def test_get_current_user_with_session():
    """Test get_current_user with user in session"""
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'test'

    with app.test_request_context():
        session['user_id'] = '123'
        with patch('utils.auth_helpers.db.session.get') as mock_get:
            mock_user = Mock()
            mock_get.return_value = mock_user
            result = get_current_user()
            assert result == mock_user


@pytest.mark.unit
def test_get_current_user_without_session():
    """Test get_current_user without user in session"""
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'test'

    with app.test_request_context():
        result = get_current_user()
        assert result is None


@pytest.mark.unit
def test_get_current_user_with_cache():
    """Test get_current_user with cached user in g"""
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'test'

    with app.test_request_context():
        session['user_id'] = '123'
        mock_user = Mock()
        g.current_user = mock_user
        result = get_current_user()
        assert result == mock_user


@pytest.mark.unit
def test_normalize_role_legacy_tenant_yoneticisi():
    """Test normalize_role with legacy tenant_yoneticisi"""
    result = normalize_role('tenant_yoneticisi')
    assert result == 'tenant_admin'


@pytest.mark.unit
def test_normalize_role_legacy_admin():
    """Test normalize_role with legacy admin"""
    result = normalize_role('admin')
    assert result == 'yonetici'


@pytest.mark.unit
def test_normalize_role_canonical_roles():
    """Test normalize_role with canonical roles"""
    assert normalize_role('sistem_yoneticisi') == 'sistem_yoneticisi'
    assert normalize_role('yonetici') == 'yonetici'
    assert normalize_role('tenant_admin') == 'tenant_admin'
    assert normalize_role('kullanici') == 'kullanici'


@pytest.mark.unit
def test_normalize_role_unknown_role():
    """Test normalize_role with unknown role"""
    result = normalize_role('unknown_role')
    assert result == 'unknown_role'


@pytest.mark.unit
def test_superadmin_required_decorator():
    """Test superadmin_required decorator"""
    assert callable(superadmin_required)

    @superadmin_required
    def protected_view():
        return 'Protected content'

    assert callable(protected_view)


@pytest.mark.unit
def test_tenant_admin_required_decorator():
    """Test tenant_admin_required decorator"""
    assert callable(tenant_admin_required)

    @tenant_admin_required
    def protected_view():
        return 'Protected content'

    assert callable(protected_view)


@pytest.mark.unit
def test_set_tenant_context_with_user():
    """Test set_tenant_context with authenticated user"""
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'test'

    with app.test_request_context():
        session['user_id'] = '123'
        with patch('utils.auth_helpers.db.session.get') as mock_get:
            mock_user = Mock()
            mock_user.tenant_id = 'tenant_123'
            mock_get.return_value = mock_user
            with patch('utils.auth_helpers.TenantContext.set'):
                result = set_tenant_context()
                assert result is None
                assert g.current_user == mock_user
                assert g.tenant_id == 'tenant_123'


@pytest.mark.unit
def test_set_tenant_context_without_user():
    """Test set_tenant_context without authenticated user"""
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'test'

    with app.test_request_context():
        with patch('utils.auth_helpers.resolve_from_request') as mock_resolve:
            mock_resolve.return_value = 'resolved_tenant'
            with patch('utils.auth_helpers.TenantContext.set'):
                result = set_tenant_context()
                assert result is None


@pytest.mark.unit
def test_set_tenant_context_user_deleted():
    """Test set_tenant_context when user is deleted"""
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'test'

    with app.test_request_context():
        session['user_id'] = '123'
        with patch('utils.auth_helpers.db.session.get') as mock_get:
            mock_get.return_value = None
            with patch('utils.auth_helpers.url_for'):
                with patch('utils.auth_helpers.redirect') as mock_redirect:
                    mock_redirect.return_value = Mock(status_code=302)
                    set_tenant_context()
                    assert mock_redirect.called


@pytest.mark.unit
def test_set_tenant_context_tenant_context_clear_exception():
    """Test set_tenant_context when TenantContext.clear raises exception"""
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'test'

    with app.test_request_context():
        session['user_id'] = '123'
        with patch('utils.auth_helpers.TenantContext.set', side_effect=RuntimeError("Test error")):
            with patch('utils.auth_helpers.db.session.get') as mock_get:
                mock_user = Mock()
                mock_user.tenant_id = 'tenant_123'
                mock_get.return_value = mock_user
                result = set_tenant_context()
                # Should not raise, exception is caught
                assert result is None


@pytest.mark.unit
def test_set_tenant_context_tenant_context_set_exception():
    """Test set_tenant_context when TenantContext.set raises exception after user set"""
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'test'

    with app.test_request_context():
        session['user_id'] = '123'
        with patch('utils.auth_helpers.db.session.get') as mock_get:
            mock_user = Mock()
            mock_user.tenant_id = 'tenant_123'
            mock_get.return_value = mock_user
            # First call to set (clear) succeeds, second call (set tenant) fails
            with patch('utils.auth_helpers.TenantContext.set') as mock_set:
                mock_set.side_effect = [None, RuntimeError("Test error")]
                result = set_tenant_context()
                # Should not raise, exception is caught
                assert result is None


@pytest.mark.unit
def test_set_tenant_context_tenant_context_set_attribute_error():
    """Test set_tenant_context when TenantContext.set raises AttributeError after user set"""
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'test'

    with app.test_request_context():
        session['user_id'] = '123'
        with patch('utils.auth_helpers.db.session.get') as mock_get:
            mock_user = Mock()
            mock_user.tenant_id = 'tenant_123'
            mock_get.return_value = mock_user
            # First call to set (clear) succeeds, second call (set tenant) fails with AttributeError
            with patch('utils.auth_helpers.TenantContext.set') as mock_set:
                mock_set.side_effect = [None, AttributeError("Test error")]
                result = set_tenant_context()
                # Should not raise, exception is caught
                assert result is None


@pytest.mark.unit
def test_set_tenant_context_resolve_from_request_exception():
    """Test set_tenant_context when resolve_from_request raises exception"""
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'test'

    with app.test_request_context():
        with patch('utils.auth_helpers.resolve_from_request', side_effect=KeyError("Test error")):
            result = set_tenant_context()
            # Should not raise, exception is caught
            assert result is None


@pytest.mark.unit
def test_set_tenant_context_resolve_from_request_no_tenant():
    """Test set_tenant_context when resolve_from_request returns None"""
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'test'

    with app.test_request_context():
        with patch('utils.auth_helpers.resolve_from_request', return_value=None):
            with patch('utils.auth_helpers.TenantContext.set') as mock_set:
                result = set_tenant_context()
                assert result is None
                # TenantContext.set is called with None when resolve returns None
                mock_set.assert_called_once_with(None)


@pytest.mark.unit
def test_set_tenant_context_resolve_from_request_success():
    """Test set_tenant_context when resolve_from_request returns tenant ID"""
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'test'

    with app.test_request_context():
        with patch('utils.auth_helpers.resolve_from_request', return_value='resolved_tenant'):
            with patch('utils.auth_helpers.TenantContext.set') as mock_set:
                result = set_tenant_context()
                assert result is None
                # TenantContext.set is called twice: once with None (clear), once with resolved tenant
                assert mock_set.call_count == 2
                mock_set.assert_any_call(None)
                mock_set.assert_any_call('resolved_tenant')


@pytest.mark.unit
def test_auth_helpers_imports():
    """Test that all auth helper functions can be imported"""
    from utils.auth_helpers import (
        get_current_user,
        login_required,
        normalize_role,
        require_role,
        set_tenant_context,
        superadmin_required,
        tenant_admin_required,
    )

    assert callable(login_required)
    assert callable(require_role)
    assert callable(get_current_user)
    assert callable(set_tenant_context)
    assert callable(superadmin_required)
    assert callable(tenant_admin_required)
    assert callable(normalize_role)


@pytest.mark.unit
def test_require_role_multiple_roles():
    """Test require_role with multiple allowed roles"""
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'test'

    @require_role('yonetici', 'sistem_yoneticisi')
    def protected_view():
        return 'Protected content'

    with app.test_request_context():
        session['user_id'] = '123'
        with patch('utils.auth_helpers.db.session.get') as mock_get:
            mock_user = Mock()
            mock_user.role = 'sistem_yoneticisi'
            mock_get.return_value = mock_user
            result = protected_view()
            assert result == 'Protected content'


@pytest.mark.unit
def test_require_role_preserves_function_metadata():
    """Test require_role preserves function metadata"""
    @require_role('yonetici')
    def protected_view():
        """Protected view docstring"""
        return 'Protected content'

    assert protected_view.__name__ == 'protected_view'
    assert protected_view.__doc__ == 'Protected view docstring'


@pytest.mark.unit
def test_login_required_preserves_function_metadata():
    """Test login_required preserves function metadata"""
    @login_required
    def protected_view():
        """Protected view docstring"""
        return 'Protected content'

    assert protected_view.__name__ == 'protected_view'
    assert protected_view.__doc__ == 'Protected view docstring'
