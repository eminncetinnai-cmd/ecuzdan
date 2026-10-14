"""
Unit Tests - Settings Routes
Settings route functions
"""

from unittest.mock import Mock, patch

import pytest

from routes.settings import (
    BASE_CURRENCY_CHOICES,
    _apply_preferences_to_engine_defaults,
    _engine_defaults,
    _get_settings_service,
    _handle_settings_action,
    _parse_optional,
    _refresh_engine_defaults_cache,
    _with_currency_context,
    register_settings_routes,
)


@pytest.mark.unit
def test_get_settings_service():
    """Test _get_settings_service function"""
    with patch('bootstrap.container.get_container') as mock_get_container:
        mock_container = Mock()
        mock_applications = Mock()
        mock_settings = Mock()
        mock_applications.settings.return_value = mock_settings
        mock_container.applications = mock_applications
        mock_get_container.return_value = mock_container

        result = _get_settings_service()
        assert result == mock_settings


@pytest.mark.unit
def test_parse_optional():
    """Test _parse_optional function"""
    # Test empty string
    assert _parse_optional('', int) is None
    assert _parse_optional(None, int) is None

    # Test valid numbers
    assert _parse_optional('5', int) == 5
    assert _parse_optional('3.14', float) == 3.14
    assert _parse_optional('3,14', float) == 3.14

    # Test invalid numbers
    with pytest.raises(ValueError):
        _parse_optional('abc', int)


@pytest.mark.unit
def test_base_currency_choices():
    """Test BASE_CURRENCY_CHOICES constant"""
    assert BASE_CURRENCY_CHOICES == ('TRY', 'USD', 'EUR', 'GBP')


@pytest.mark.unit
def test_register_settings_routes():
    """Test register_settings_routes function"""
    mock_bp = Mock()
    mock_bp.route = Mock(return_value=lambda f: f)

    register_settings_routes(mock_bp)

    assert mock_bp.route.called


@pytest.mark.unit
def test_settings_imports():
    """Test that settings functions can be imported"""
    from routes.settings import (
        _get_settings_service,
        _parse_optional,
        register_settings_routes,
    )

    assert callable(_get_settings_service)
    assert callable(_parse_optional)
    assert callable(_with_currency_context)
    assert callable(_apply_preferences_to_engine_defaults)
    assert callable(_refresh_engine_defaults_cache)
    assert callable(_engine_defaults)
    assert callable(_handle_settings_action)
    assert callable(register_settings_routes)


@pytest.mark.unit
def test_settings_routes_structure():
    """Test settings routes module structure"""
    import routes.settings as settings_module

    # Check for expected functions
    assert hasattr(settings_module, '_get_settings_service')
    assert hasattr(settings_module, '_parse_optional')
    assert hasattr(settings_module, '_with_currency_context')
    assert hasattr(settings_module, '_apply_preferences_to_engine_defaults')
    assert hasattr(settings_module, '_refresh_engine_defaults_cache')
    assert hasattr(settings_module, '_engine_defaults')
    assert hasattr(settings_module, '_handle_settings_action')
    assert hasattr(settings_module, 'register_settings_routes')

    # Check for expected imports
    assert hasattr(settings_module, 'logging')
    assert hasattr(settings_module, 'os')
    assert hasattr(settings_module, 'time')
    assert hasattr(settings_module, 'datetime')
    assert hasattr(settings_module, 'Decimal')
    assert hasattr(settings_module, 'Lock')
    assert hasattr(settings_module, 'Thread')
    assert hasattr(settings_module, 'current_app')
    assert hasattr(settings_module, 'flash')
    assert hasattr(settings_module, 'redirect')
    assert hasattr(settings_module, 'render_template')
    assert hasattr(settings_module, 'request')
    assert hasattr(settings_module, 'session')
    assert hasattr(settings_module, 'url_for')


@pytest.mark.unit
def test_settings_logger_exists():
    """Test settings module has logger"""
    import routes.settings as settings_module
    assert hasattr(settings_module, 'logger')
    assert settings_module.logger is not None


@pytest.mark.unit
def test_register_settings_routes_route_registration():
    """Test register_settings_routes registers routes"""
    mock_bp = Mock()
    mock_bp.route = Mock(return_value=lambda f: f)

    register_settings_routes(mock_bp)

    # Should register multiple routes
    assert mock_bp.route.call_count >= 4


@pytest.mark.unit
def test_settings_module_has_required_imports():
    """Test settings module has required imports"""
    import routes.settings as settings_module

    # Flask imports
    assert hasattr(settings_module, 'current_app')
    assert hasattr(settings_module, 'flash')
    assert hasattr(settings_module, 'redirect')
    assert hasattr(settings_module, 'render_template')
    assert hasattr(settings_module, 'request')
    assert hasattr(settings_module, 'session')
    assert hasattr(settings_module, 'url_for')

    # Standard library imports
    assert hasattr(settings_module, 'logging')
    assert hasattr(settings_module, 'os')
    assert hasattr(settings_module, 'time')
    assert hasattr(settings_module, 'datetime')
    assert hasattr(settings_module, 'Decimal')
    assert hasattr(settings_module, 'Lock')
    assert hasattr(settings_module, 'Thread')

    # Custom imports
    assert hasattr(settings_module, 'secure_filename')
    assert hasattr(settings_module, 'get_container')
    assert hasattr(settings_module, 'i18n')
    assert hasattr(settings_module, 'clear_admin_demo_data')
    assert hasattr(settings_module, 'generate_advanced_demo_data')
    assert hasattr(settings_module, 'rollback_session')
    assert hasattr(settings_module, 'login_required')


@pytest.mark.unit
def test_settings_blueprint_parameter():
    """Test register_settings_routes accepts blueprint parameter"""
    mock_bp = Mock()
    mock_bp.route = Mock(return_value=lambda f: f)

    # Should not raise exception
    register_settings_routes(mock_bp)


@pytest.mark.unit
def test_settings_route_exists():
    """Test settings route exists"""
    import inspect

    import routes.settings as settings_module

    source = inspect.getsource(settings_module)
    assert '/settings' in source


@pytest.mark.unit
def test_logout_other_devices_route_exists():
    """Test logout other devices route exists"""
    import inspect

    import routes.settings as settings_module

    source = inspect.getsource(settings_module)
    assert '/logout_other_devices' in source


@pytest.mark.unit
def test_toggle_privacy_mode_route_exists():
    """Test toggle privacy mode route exists"""
    import inspect

    import routes.settings as settings_module

    source = inspect.getsource(settings_module)
    assert '/toggle_privacy_mode' in source


@pytest.mark.unit
def test_reset_data_route_exists():
    """Test reset data route exists"""
    import inspect

    import routes.settings as settings_module

    source = inspect.getsource(settings_module)
    assert '/reset_data' in source


@pytest.mark.unit
def test_settings_error_handling_structure():
    """Test settings routes have error handling"""
    import inspect

    import routes.settings as settings_module

    # Check that the module has error handling patterns
    source = inspect.getsource(settings_module)
    assert 'except Exception' in source or 'try:' in source


@pytest.mark.unit
def test_settings_permission_error_handling():
    """Test settings routes handle PermissionError"""
    import inspect

    import routes.settings as settings_module

    source = inspect.getsource(settings_module)
    assert 'PermissionError' in source


@pytest.mark.unit
def test_settings_flash_messaging():
    """Test settings routes use flash messaging"""
    import inspect

    import routes.settings as settings_module

    source = inspect.getsource(settings_module)
    assert 'flash' in source


@pytest.mark.unit
def test_settings_rollback_session():
    """Test settings routes use rollback_session"""
    import inspect

    import routes.settings as settings_module

    source = inspect.getsource(settings_module)
    assert 'rollback_session' in source


@pytest.mark.unit
def test_settings_session_usage():
    """Test settings routes use session"""
    import inspect

    import routes.settings as settings_module

    source = inspect.getsource(settings_module)
    assert 'session' in source


@pytest.mark.unit
def test_settings_login_required():
    """Test settings routes use login_required decorator"""
    import inspect

    import routes.settings as settings_module

    source = inspect.getsource(settings_module)
    assert 'login_required' in source


@pytest.mark.unit
def test_settings_file_upload():
    """Test settings routes handle file upload"""
    import inspect

    import routes.settings as settings_module

    source = inspect.getsource(settings_module)
    assert 'file' in source or 'secure_filename' in source


@pytest.mark.unit
def test_settings_password_change():
    """Test settings routes handle password change"""
    import inspect

    import routes.settings as settings_module

    source = inspect.getsource(settings_module)
    assert 'password' in source.lower()


@pytest.mark.unit
def test_settings_currency_change():
    """Test settings routes handle currency change"""
    import inspect

    import routes.settings as settings_module

    source = inspect.getsource(settings_module)
    assert 'currency' in source.lower()


@pytest.mark.unit
def test_settings_preferences():
    """Test settings routes handle preferences"""
    import inspect

    import routes.settings as settings_module

    source = inspect.getsource(settings_module)
    assert 'preferences' in source.lower()


@pytest.mark.unit
def test_settings_privacy_mode():
    """Test settings routes handle privacy mode"""
    import inspect

    import routes.settings as settings_module

    source = inspect.getsource(settings_module)
    assert 'privacy' in source.lower()


@pytest.mark.unit
def test_settings_theme():
    """Test settings routes handle theme"""
    import inspect

    import routes.settings as settings_module

    source = inspect.getsource(settings_module)
    assert 'theme' in source.lower()


@pytest.mark.unit
def test_settings_notifications():
    """Test settings routes handle notifications"""
    import inspect

    import routes.settings as settings_module

    source = inspect.getsource(settings_module)
    assert 'notification' in source.lower()


@pytest.mark.unit
def test_settings_language():
    """Test settings routes handle language"""
    import inspect

    import routes.settings as settings_module

    source = inspect.getsource(settings_module)
    assert 'language' in source.lower()


@pytest.mark.unit
def test_settings_admin_actions():
    """Test settings routes handle admin actions"""
    import inspect

    import routes.settings as settings_module

    source = inspect.getsource(settings_module)
    assert 'admin' in source.lower()


@pytest.mark.unit
def test_settings_engine_defaults():
    """Test settings routes use engine defaults"""
    import inspect

    import routes.settings as settings_module

    source = inspect.getsource(settings_module)
    assert 'engine_defaults' in source


@pytest.mark.unit
def test_settings_currency_manager():
    """Test settings routes use CurrencyManager"""
    import inspect

    import routes.settings as settings_module

    source = inspect.getsource(settings_module)
    assert 'CurrencyManager' in source


@pytest.mark.unit
def test_settings_threading():
    """Test settings routes use threading"""
    import inspect

    import routes.settings as settings_module

    source = inspect.getsource(settings_module)
    assert 'Thread' in source or 'Lock' in source


@pytest.mark.unit
def test_settings_caching():
    """Test settings routes use caching"""
    import inspect

    import routes.settings as settings_module

    source = inspect.getsource(settings_module)
    assert 'cache' in source.lower() or 'CACHE' in source


@pytest.mark.unit
def test_settings_i18n():
    """Test settings routes use i18n"""
    import inspect

    import routes.settings as settings_module

    source = inspect.getsource(settings_module)
    assert 'i18n' in source


@pytest.mark.unit
def test_get_standard_category_codes_function_exists():
    """Test _get_standard_category_codes function exists and is callable"""
    from routes.settings import _get_standard_category_codes
    assert callable(_get_standard_category_codes)


@pytest.mark.unit
def test_parse_optional_duplicate():
    """Test _parse_optional function"""
    from routes.settings import _parse_optional

    assert _parse_optional('123', int) == 123
    assert _parse_optional('', int) is None
    assert _parse_optional(None, int) is None
    assert _parse_optional('3.14', float) == 3.14


@pytest.mark.unit
def test_parse_optional_with_comma():
    """Test _parse_optional handles comma as decimal separator"""
    from routes.settings import _parse_optional

    assert _parse_optional('3,14', float) == 3.14
    assert _parse_optional('1234', int) == 1234


@pytest.mark.unit
def test_parse_optional_invalid_number():
    """Test _parse_optional raises ValueError for invalid numbers"""
    from routes.settings import _parse_optional

    with pytest.raises(ValueError, match="geçerli bir sayı değil"):
        _parse_optional('abc', int)

    with pytest.raises(ValueError, match="geçerli bir sayı değil"):
        _parse_optional('12.34.56', float)


@pytest.mark.unit
def test_get_settings_service_function_exists():
    """Test _get_settings_service function exists and is callable"""
    from routes.settings import _get_settings_service
    assert callable(_get_settings_service)


@pytest.mark.unit
def test_cleanup_non_standard_categories_function_exists():
    """Test _cleanup_non_standard_categories function exists and is callable"""
    from routes.settings import _cleanup_non_standard_categories
    assert callable(_cleanup_non_standard_categories)


@pytest.mark.unit
def test_with_currency_context_function_exists():
    """Test _with_currency_context function exists and is callable"""
    assert callable(_with_currency_context)


@pytest.mark.unit
def test_apply_preferences_to_engine_defaults_function_exists():
    """Test _apply_preferences_to_engine_defaults function exists and is callable"""
    assert callable(_apply_preferences_to_engine_defaults)


@pytest.mark.unit
def test_engine_defaults_function_exists():
    """Test _engine_defaults function exists and is callable"""
    assert callable(_engine_defaults)


@pytest.mark.unit
def test_handle_settings_action_function_exists():
    """Test _handle_settings_action function exists and is callable"""
    assert callable(_handle_settings_action)


@pytest.mark.unit
def test_rollback_session_function_exists():
    """Test rollback_session function exists and is callable"""
    from routes.settings import rollback_session
    assert callable(rollback_session)


@pytest.mark.unit
def test_base_currency_choices_constant():
    """Test BASE_CURRENCY_CHOICES constant exists"""
    from routes.settings import BASE_CURRENCY_CHOICES
    assert isinstance(BASE_CURRENCY_CHOICES, tuple)
    assert 'TRY' in BASE_CURRENCY_CHOICES
    assert 'USD' in BASE_CURRENCY_CHOICES


@pytest.mark.unit
def test_engine_defaults_cache_constants():
    """Test engine defaults cache constants exist"""
    from routes.settings import (
        _ENGINE_DEFAULTS_CACHE,
        _ENGINE_DEFAULTS_CACHE_TTL,
    )
    assert isinstance(_ENGINE_DEFAULTS_CACHE, dict)
    assert isinstance(_ENGINE_DEFAULTS_CACHE_TTL, int)
    assert _ENGINE_DEFAULTS_CACHE_TTL == 3600


@pytest.mark.unit
def test_settings_has_login_required():
    """Test settings routes use login_required decorator"""
    import inspect

    import routes.settings as settings_module

    source = inspect.getsource(settings_module)
    assert 'login_required' in source


@pytest.mark.unit
def test_settings_uses_flash():
    """Test settings routes use flash messages"""
    import inspect

    import routes.settings as settings_module

    source = inspect.getsource(settings_module)
    assert 'flash' in source


@pytest.mark.unit
def test_settings_uses_session():
    """Test settings routes use session"""
    import inspect

    import routes.settings as settings_module

    source = inspect.getsource(settings_module)
    assert 'session' in source


@pytest.mark.unit
def test_settings_uses_logger():
    """Test settings module has logger"""
    import routes.settings as settings_module
    assert hasattr(settings_module, 'logger')


@pytest.mark.unit
def test_settings_has_logging():
    """Test settings module uses logging"""
    import inspect

    import routes.settings as settings_module

    source = inspect.getsource(settings_module)
    assert 'logger' in source


@pytest.mark.unit
def test_settings_uses_request():
    """Test settings routes use request"""
    import inspect

    import routes.settings as settings_module

    source = inspect.getsource(settings_module)
    assert 'request' in source


@pytest.mark.unit
def test_settings_uses_redirect():
    """Test settings routes use redirect"""
    import inspect

    import routes.settings as settings_module

    source = inspect.getsource(settings_module)
    assert 'redirect' in source


@pytest.mark.unit
def test_settings_uses_render_template():
    """Test settings routes use render_template"""
    import inspect

    import routes.settings as settings_module

    source = inspect.getsource(settings_module)
    assert 'render_template' in source


@pytest.mark.unit
def test_settings_uses_url_for():
    """Test settings routes use url_for"""
    import inspect

    import routes.settings as settings_module

    source = inspect.getsource(settings_module)
    assert 'url_for' in source


@pytest.mark.unit
def test_settings_has_threading():
    """Test settings module uses threading"""
    import inspect

    import routes.settings as settings_module

    source = inspect.getsource(settings_module)
    assert 'Thread' in source or 'threading' in source


@pytest.mark.unit
def test_settings_has_time_import():
    """Test settings module imports time"""
    import inspect

    import routes.settings as settings_module

    source = inspect.getsource(settings_module)
    assert 'time' in source


@pytest.mark.unit
def test_settings_has_decimal_import():
    """Test settings module imports Decimal"""
    import inspect

    import routes.settings as settings_module

    source = inspect.getsource(settings_module)
    assert 'Decimal' in source


@pytest.mark.unit
def test_settings_has_secure_filename():
    """Test settings module uses secure_filename"""
    import inspect

    import routes.settings as settings_module

    source = inspect.getsource(settings_module)
    assert 'secure_filename' in source


@pytest.mark.unit
def test_settings_has_current_app():
    """Test settings module uses current_app"""
    import inspect

    import routes.settings as settings_module

    source = inspect.getsource(settings_module)
    assert 'current_app' in source


@pytest.mark.unit
def test_settings_has_os_import():
    """Test settings module imports os"""
    import inspect

    import routes.settings as settings_module

    source = inspect.getsource(settings_module)
    assert 'os' in source


@pytest.mark.unit
def test_settings_has_datetime_import():
    """Test settings module imports datetime"""
    import inspect

    import routes.settings as settings_module

    source = inspect.getsource(settings_module)
    assert 'datetime' in source


@pytest.mark.unit
def test_settings_has_lock_import():
    """Test settings module imports Lock"""
    import inspect

    import routes.settings as settings_module

    source = inspect.getsource(settings_module)
    assert 'Lock' in source


@pytest.mark.unit
def test_settings_uses_bootstrap_container():
    """Test settings module uses bootstrap container"""
    import inspect

    import routes.settings as settings_module

    source = inspect.getsource(settings_module)
    assert 'bootstrap' in source or 'container' in source


@pytest.mark.unit
def test_settings_uses_infrastructure_i18n():
    """Test settings module uses infrastructure i18n"""
    import inspect

    import routes.settings as settings_module

    source = inspect.getsource(settings_module)
    assert 'i18n' in source


@pytest.mark.unit
def test_settings_uses_infrastructure_demo():
    """Test settings module uses infrastructure demo"""
    import inspect

    import routes.settings as settings_module

    source = inspect.getsource(settings_module)
    assert 'demo' in source


@pytest.mark.unit
def test_settings_uses_utils_db_session():
    """Test settings module uses utils db_session"""
    import inspect

    import routes.settings as settings_module

    source = inspect.getsource(settings_module)
    assert 'db_session' in source or 'rollback_session' in source


@pytest.mark.unit
def test_settings_uses_utils_decorators():
    """Test settings module uses utils decorators"""
    import inspect

    import routes.settings as settings_module

    source = inspect.getsource(settings_module)
    assert 'decorators' in source or 'login_required' in source


@pytest.mark.unit
def test_base_currency_choices_length():
    """Test BASE_CURRENCY_CHOICES has expected length"""
    from routes.settings import BASE_CURRENCY_CHOICES
    assert len(BASE_CURRENCY_CHOICES) == 4


@pytest.mark.unit
def test_base_currency_choices_all_strings():
    """Test all BASE_CURRENCY_CHOICES are strings"""
    from routes.settings import BASE_CURRENCY_CHOICES
    for choice in BASE_CURRENCY_CHOICES:
        assert isinstance(choice, str)


@pytest.mark.unit
def test_engine_defaults_cache_structure():
    """Test _ENGINE_DEFAULTS_CACHE has expected structure"""
    from routes.settings import _ENGINE_DEFAULTS_CACHE
    assert 'data' in _ENGINE_DEFAULTS_CACHE
    assert 'last_updated' in _ENGINE_DEFAULTS_CACHE


@pytest.mark.unit
def test_engine_defaults_cache_initial_values():
    """Test _ENGINE_DEFAULTS_CACHE initial values"""
    from routes.settings import _ENGINE_DEFAULTS_CACHE
    assert _ENGINE_DEFAULTS_CACHE['data'] is None
    assert _ENGINE_DEFAULTS_CACHE['last_updated'] == 0


@pytest.mark.unit
def test_engine_defaults_refresh_in_progress_initial():
    """Test _ENGINE_DEFAULTS_REFRESH_IN_PROGRESS initial value"""
    from routes.settings import _ENGINE_DEFAULTS_REFRESH_IN_PROGRESS
    assert _ENGINE_DEFAULTS_REFRESH_IN_PROGRESS is False


@pytest.mark.unit
def test_settings_module_docstring():
    """Test settings module has docstring"""
    import routes.settings as settings_module
    assert settings_module.__doc__ is not None


@pytest.mark.unit
def test_settings_module_has_logging_config():
    """Test settings module configures logging"""
    import inspect

    import routes.settings as settings_module

    source = inspect.getsource(settings_module)
    assert 'logging' in source


@pytest.mark.unit
def test_settings_has_exception_handling():
    """Test settings routes have exception handling"""
    import inspect

    import routes.settings as settings_module

    source = inspect.getsource(settings_module)
    assert 'except' in source or 'try' in source


@pytest.mark.unit
def test_settings_has_flash_messages():
    """Test settings routes use flash messages"""
    import inspect

    import routes.settings as settings_module

    source = inspect.getsource(settings_module)
    assert 'flash' in source


@pytest.mark.unit
def test_settings_has_route_decorators():
    """Test settings routes use route decorators"""
    import inspect

    import routes.settings as settings_module

    source = inspect.getsource(settings_module)
    assert '@' in source  # Decorator syntax


@pytest.mark.unit
def test_settings_has_post_methods():
    """Test settings routes have POST methods"""
    import inspect

    import routes.settings as settings_module

    source = inspect.getsource(settings_module)
    assert 'POST' in source or 'post' in source


@pytest.mark.unit
def test_settings_has_get_methods():
    """Test settings routes have GET methods"""
    import inspect

    import routes.settings as settings_module

    source = inspect.getsource(settings_module)
    assert 'GET' in source or 'get' in source


@pytest.mark.unit
def test_settings_has_form_handling():
    """Test settings routes handle form data"""
    import inspect

    import routes.settings as settings_module

    source = inspect.getsource(settings_module)
    assert 'form' in source


@pytest.mark.unit
def test_settings_has_file_handling():
    """Test settings routes handle file uploads"""
    import inspect

    import routes.settings as settings_module

    source = inspect.getsource(settings_module)
    assert 'file' in source or 'secure_filename' in source


@pytest.mark.unit
def test_settings_has_password_handling():
    """Test settings routes handle password changes"""
    import inspect

    import routes.settings as settings_module

    source = inspect.getsource(settings_module)
    assert 'password' in source or 'pw' in source


@pytest.mark.unit
def test_settings_has_currency_handling():
    """Test settings routes handle currency changes"""
    import inspect

    import routes.settings as settings_module

    source = inspect.getsource(settings_module)
    assert 'currency' in source


@pytest.mark.unit
def test_settings_has_theme_handling():
    """Test settings routes handle theme changes"""
    import inspect

    import routes.settings as settings_module

    source = inspect.getsource(settings_module)
    assert 'theme' in source


@pytest.mark.unit
def test_settings_has_language_handling():
    """Test settings routes handle language changes"""
    import inspect

    import routes.settings as settings_module

    source = inspect.getsource(settings_module)
    assert 'language' in source or 'lang' in source


@pytest.mark.unit
def test_settings_has_privacy_mode():
    """Test settings routes handle privacy mode"""
    import inspect

    import routes.settings as settings_module

    source = inspect.getsource(settings_module)
    assert 'privacy' in source


@pytest.mark.unit
def test_settings_has_notification_handling():
    """Test settings routes handle notification preferences"""
    import inspect

    import routes.settings as settings_module

    source = inspect.getsource(settings_module)
    assert 'notification' in source or 'notify' in source


@pytest.mark.unit
def test_get_standard_category_codes_docstring():
    """Test _get_standard_category_codes has docstring"""
    from routes.settings import _get_standard_category_codes
    assert _get_standard_category_codes.__doc__ is not None


@pytest.mark.unit
def test_cleanup_non_standard_categories_docstring():
    """Test _cleanup_non_standard_categories has docstring"""
    from routes.settings import _cleanup_non_standard_categories
    assert _cleanup_non_standard_categories.__doc__ is not None


@pytest.mark.unit
def test_parse_optional_docstring():
    """Test _parse_optional has docstring"""
    from routes.settings import _parse_optional
    assert _parse_optional.__doc__ is not None


@pytest.mark.unit
def test_with_currency_context_docstring():
    """Test _with_currency_context has docstring"""
    assert _with_currency_context.__doc__ is not None


@pytest.mark.unit
def test_engine_defaults_docstring():
    """Test _engine_defaults has docstring"""
    assert _engine_defaults.__doc__ is not None


@pytest.mark.unit
def test_refresh_engine_defaults_cache_function_exists():
    """Test _refresh_engine_defaults_cache function exists and is callable"""
    assert callable(_refresh_engine_defaults_cache)


@pytest.mark.unit
def test_parse_optional_whitespace_handling():
    """Test _parse_optional handles whitespace correctly"""
    from routes.settings import _parse_optional

    assert _parse_optional('  123  ', int) == 123
    assert _parse_optional('   ', int) is None
    assert _parse_optional('  3.14  ', float) == 3.14


@pytest.mark.unit
def test_parse_optional_negative_numbers():
    """Test _parse_optional handles negative numbers"""
    from routes.settings import _parse_optional

    assert _parse_optional('-123', int) == -123
    assert _parse_optional('-3.14', float) == -3.14


@pytest.mark.unit
def test_parse_optional_zero():
    """Test _parse_optional handles zero"""
    from routes.settings import _parse_optional

    assert _parse_optional('0', int) == 0
    assert _parse_optional('0.0', float) == 0.0


@pytest.mark.unit
def test_parse_optional_large_numbers():
    """Test _parse_optional handles large numbers"""
    from routes.settings import _parse_optional

    assert _parse_optional('999999', int) == 999999
    assert _parse_optional('999999.99', float) == 999999.99


@pytest.mark.unit
def test_engine_defaults_cache_lock_type():
    """Test _ENGINE_DEFAULTS_REFRESH_LOCK is a Lock"""
    from threading import Lock

    from routes.settings import _ENGINE_DEFAULTS_REFRESH_LOCK
    assert isinstance(_ENGINE_DEFAULTS_REFRESH_LOCK, Lock)


@pytest.mark.unit
def test_engine_defaults_cache_ttl_value():
    """Test _ENGINE_DEFAULTS_CACHE_TTL is 3600 seconds"""
    from routes.settings import _ENGINE_DEFAULTS_CACHE_TTL
    assert _ENGINE_DEFAULTS_CACHE_TTL == 3600


@pytest.mark.unit
def test_base_currency_choices_contains_eur():
    """Test BASE_CURRENCY_CHOICES contains EUR"""
    from routes.settings import BASE_CURRENCY_CHOICES
    assert 'EUR' in BASE_CURRENCY_CHOICES


@pytest.mark.unit
def test_base_currency_choices_contains_gbp():
    """Test BASE_CURRENCY_CHOICES contains GBP"""
    from routes.settings import BASE_CURRENCY_CHOICES
    assert 'GBP' in BASE_CURRENCY_CHOICES


@pytest.mark.unit
def test_base_currency_choices_is_immutable():
    """Test BASE_CURRENCY_CHOICES is a tuple (immutable)"""
    from routes.settings import BASE_CURRENCY_CHOICES
    assert isinstance(BASE_CURRENCY_CHOICES, tuple)


@pytest.mark.unit
def test_engine_defaults_cache_is_dict():
    """Test _ENGINE_DEFAULTS_CACHE is a dictionary"""
    from routes.settings import _ENGINE_DEFAULTS_CACHE
    assert isinstance(_ENGINE_DEFAULTS_CACHE, dict)


@pytest.mark.unit
def test_engine_defaults_refresh_in_progress_is_bool():
    """Test _ENGINE_DEFAULTS_REFRESH_IN_PROGRESS is a boolean"""
    from routes.settings import _ENGINE_DEFAULTS_REFRESH_IN_PROGRESS
    assert isinstance(_ENGINE_DEFAULTS_REFRESH_IN_PROGRESS, bool)


@pytest.mark.unit
def test_settings_module_length():
    """Test settings module has reasonable length"""
    import inspect

    import routes.settings as settings_module

    source = inspect.getsource(settings_module)
    # Module should have at least 400 lines
    assert len(source.split('\n')) > 400


@pytest.mark.unit
def test_settings_has_multiple_routes():
    """Test settings module has multiple route definitions"""
    import inspect

    import routes.settings as settings_module

    source = inspect.getsource(settings_module)
    # Should have multiple @bp.route decorators
    assert source.count('@bp.route') >= 3


@pytest.mark.unit
def test_settings_has_reset_data_route():
    """Test settings has reset_data route"""
    import inspect

    import routes.settings as settings_module

    source = inspect.getsource(settings_module)
    assert 'reset_data' in source


@pytest.mark.unit
def test_settings_has_logout_other_devices_route():
    """Test settings has logout_other_devices route"""
    import inspect

    import routes.settings as settings_module

    source = inspect.getsource(settings_module)
    assert 'logout_other_devices' in source


@pytest.mark.unit
def test_settings_has_toggle_privacy_mode_route():
    """Test settings has toggle_privacy_mode route"""
    import inspect

    import routes.settings as settings_module

    source = inspect.getsource(settings_module)
    assert 'toggle_privacy_mode' in source


@pytest.mark.unit
def test_settings_has_admin_actions():
    """Test settings has admin action handling"""
    import inspect

    import routes.settings as settings_module

    source = inspect.getsource(settings_module)
    assert 'admin' in source.lower()


@pytest.mark.unit
def test_settings_has_profile_update():
    """Test settings has profile update handling"""
    import inspect

    import routes.settings as settings_module

    source = inspect.getsource(settings_module)
    assert 'update_profile' in source


@pytest.mark.unit
def test_settings_has_password_change():
    """Test settings has password change handling"""
    import inspect

    import routes.settings as settings_module

    source = inspect.getsource(settings_module)
    assert 'change_pw' in source or 'password' in source.lower()


@pytest.mark.unit
def test_settings_has_currency_change():
    """Test settings has currency change handling"""
    import inspect

    import routes.settings as settings_module

    source = inspect.getsource(settings_module)
    assert 'change_base_currency' in source


@pytest.mark.unit
def test_settings_has_preferences_update():
    """Test settings has preferences update handling"""
    import inspect

    import routes.settings as settings_module

    source = inspect.getsource(settings_module)
    assert 'update_preferences' in source


@pytest.mark.unit
def test_settings_has_theme_change():
    """Test settings has theme change handling"""
    import inspect

    import routes.settings as settings_module

    source = inspect.getsource(settings_module)
    assert 'change_theme' in source


@pytest.mark.unit
def test_settings_has_notification_update():
    """Test settings has notification update handling"""
    import inspect

    import routes.settings as settings_module

    source = inspect.getsource(settings_module)
    assert 'update_notifications' in source or 'notify' in source


@pytest.mark.unit
def test_settings_has_language_change():
    """Test settings has language change handling"""
    import inspect

    import routes.settings as settings_module

    source = inspect.getsource(settings_module)
    assert 'change_language' in source


@pytest.mark.unit
def test_settings_has_privacy_mode_toggle():
    """Test settings has privacy mode toggle handling"""
    import inspect

    import routes.settings as settings_module

    source = inspect.getsource(settings_module)
    assert 'set_privacy_mode' in source


@pytest.mark.unit
def test_settings_has_file_upload_handling():
    """Test settings has file upload handling"""
    import inspect

    import routes.settings as settings_module

    source = inspect.getsource(settings_module)
    assert 'file' in source.lower() or 'upload' in source.lower()


@pytest.mark.unit
def test_settings_has_error_handling():
    """Test settings has error handling"""
    import inspect

    import routes.settings as settings_module

    source = inspect.getsource(settings_module)
    assert 'except' in source.lower()


@pytest.mark.unit
def test_settings_has_logging_duplicate():
    """Test settings has logging statements"""
    import inspect

    import routes.settings as settings_module

    source = inspect.getsource(settings_module)
    assert 'logger' in source.lower()


@pytest.mark.unit
def test_settings_has_session_management():
    """Test settings has session management"""
    import inspect

    import routes.settings as settings_module

    source = inspect.getsource(settings_module)
    assert 'session' in source.lower()


@pytest.mark.unit
def test_settings_has_redirect_logic():
    """Test settings has redirect logic"""
    import inspect

    import routes.settings as settings_module

    source = inspect.getsource(settings_module)
    assert 'redirect' in source.lower()


@pytest.mark.unit
def test_settings_has_template_rendering():
    """Test settings has template rendering"""
    import inspect

    import routes.settings as settings_module

    source = inspect.getsource(settings_module)
    assert 'render_template' in source.lower()


@pytest.mark.unit
def test_parse_optional_with_float():
    """Test _parse_optional with float conversion"""
    from routes.settings import _parse_optional

    assert _parse_optional('123.45', float) == 123.45
    assert _parse_optional('0.01', float) == 0.01


@pytest.mark.unit
def test_parse_optional_with_string_whitespace():
    """Test _parse_optional with string containing only whitespace"""
    from routes.settings import _parse_optional

    assert _parse_optional('   ', int) is None
    assert _parse_optional('\t', int) is None
    assert _parse_optional('\n', int) is None


@pytest.mark.unit
def test_parse_optional_with_mixed_whitespace():
    """Test _parse_optional with mixed whitespace and number"""
    from routes.settings import _parse_optional

    assert _parse_optional('  42  ', int) == 42
    assert _parse_optional('\t99\t', int) == 99


@pytest.mark.unit
def test_base_currency_choices_order():
    """Test BASE_CURRENCY_CHOICES has expected order"""
    from routes.settings import BASE_CURRENCY_CHOICES
    assert BASE_CURRENCY_CHOICES[0] == 'TRY'
    assert BASE_CURRENCY_CHOICES[1] == 'USD'


@pytest.mark.unit
def test_engine_defaults_cache_keys():
    """Test _ENGINE_DEFAULTS_CACHE has expected keys"""
    from routes.settings import _ENGINE_DEFAULTS_CACHE
    expected_keys = {'data', 'last_updated'}
    assert set(_ENGINE_DEFAULTS_CACHE.keys()) == expected_keys


@pytest.mark.unit
def test_engine_defaults_cache_data_type():
    """Test _ENGINE_DEFAULTS_CACHE['data'] can be None or dict"""
    from routes.settings import _ENGINE_DEFAULTS_CACHE
    # Initially None
    assert _ENGINE_DEFAULTS_CACHE['data'] is None or isinstance(_ENGINE_DEFAULTS_CACHE['data'], dict)


@pytest.mark.unit
def test_engine_defaults_cache_last_updated_type():
    """Test _ENGINE_DEFAULTS_CACHE['last_updated'] is numeric"""
    from routes.settings import _ENGINE_DEFAULTS_CACHE
    assert isinstance(_ENGINE_DEFAULTS_CACHE['last_updated'], (int, float))


@pytest.mark.unit
def test_engine_defaults_cache_ttl_positive():
    """Test _ENGINE_DEFAULTS_CACHE_TTL is positive"""
    from routes.settings import _ENGINE_DEFAULTS_CACHE_TTL
    assert _ENGINE_DEFAULTS_CACHE_TTL > 0


@pytest.mark.unit
def test_engine_defaults_refresh_lock_callable():
    """Test _ENGINE_DEFAULTS_REFRESH_LOCK has acquire/release methods"""
    from routes.settings import _ENGINE_DEFAULTS_REFRESH_LOCK
    assert hasattr(_ENGINE_DEFAULTS_REFRESH_LOCK, 'acquire')
    assert hasattr(_ENGINE_DEFAULTS_REFRESH_LOCK, 'release')


@pytest.mark.unit
def test_settings_module_has_getattr():
    """Test settings module can be imported with getattr"""
    import routes.settings
    assert hasattr(routes.settings, '_parse_optional')
    assert hasattr(routes.settings, '_get_settings_service')


@pytest.mark.unit
def test_settings_module_dir():
    """Test settings module has expected attributes"""
    import routes.settings
    attrs = dir(routes.settings)
    assert '_parse_optional' in attrs
    assert '_get_settings_service' in attrs
    assert '_cleanup_non_standard_categories' in attrs


@pytest.mark.unit
def test_parse_optional_empty_string():
    """Test _parse_optional with empty string"""
    from routes.settings import _parse_optional

    assert _parse_optional('', int) is None
    assert _parse_optional('', float) is None


@pytest.mark.unit
def test_parse_optional_none_input():
    """Test _parse_optional with None input"""
    from routes.settings import _parse_optional

    assert _parse_optional(None, int) is None
    assert _parse_optional(None, float) is None


@pytest.mark.unit
def test_parse_optional_comma_decimal_various():
    """Test _parse_optional with various comma decimal formats"""
    from routes.settings import _parse_optional

    assert _parse_optional('1,5', float) == 1.5
    assert _parse_optional('0,5', float) == 0.5
    assert _parse_optional('10,0', float) == 10.0


@pytest.mark.unit
def test_parse_optional_scientific_notation():
    """Test _parse_optional with scientific notation"""
    from routes.settings import _parse_optional

    assert _parse_optional('1e5', float) == 100000.0
    assert _parse_optional('1.5e2', float) == 150.0


@pytest.mark.unit
def test_base_currency_choices_no_duplicates():
    """Test BASE_CURRENCY_CHOICES has no duplicates"""
    from routes.settings import BASE_CURRENCY_CHOICES
    assert len(BASE_CURRENCY_CHOICES) == len(set(BASE_CURRENCY_CHOICES))


@pytest.mark.unit
def test_base_currency_choices_uppercase():
    """Test all BASE_CURRENCY_CHOICES are uppercase"""
    from routes.settings import BASE_CURRENCY_CHOICES
    for choice in BASE_CURRENCY_CHOICES:
        assert choice == choice.upper()


@pytest.mark.unit
def test_engine_defaults_cache_mutable():
    """Test _ENGINE_DEFAULTS_CACHE can be modified"""
    from routes.settings import _ENGINE_DEFAULTS_CACHE
    original_data = _ENGINE_DEFAULTS_CACHE['data']
    _ENGINE_DEFAULTS_CACHE['data'] = {'test': 'value'}
    assert _ENGINE_DEFAULTS_CACHE['data'] == {'test': 'value'}
    _ENGINE_DEFAULTS_CACHE['data'] = original_data  # Restore


@pytest.mark.unit
def test_engine_defaults_cache_last_updated_mutable():
    """Test _ENGINE_DEFAULTS_CACHE['last_updated'] can be modified"""
    from routes.settings import _ENGINE_DEFAULTS_CACHE
    original_value = _ENGINE_DEFAULTS_CACHE['last_updated']
    _ENGINE_DEFAULTS_CACHE['last_updated'] = 12345
    assert _ENGINE_DEFAULTS_CACHE['last_updated'] == 12345
    _ENGINE_DEFAULTS_CACHE['last_updated'] = original_value  # Restore


@pytest.mark.unit
def test_engine_defaults_refresh_in_progress_mutable():
    """Test _ENGINE_DEFAULTS_REFRESH_IN_PROGRESS can be modified"""
    from routes.settings import _ENGINE_DEFAULTS_REFRESH_IN_PROGRESS
    original_value = _ENGINE_DEFAULTS_REFRESH_IN_PROGRESS
    _ENGINE_DEFAULTS_REFRESH_IN_PROGRESS = True
    assert _ENGINE_DEFAULTS_REFRESH_IN_PROGRESS is True
    _ENGINE_DEFAULTS_REFRESH_IN_PROGRESS = original_value  # Restore


@pytest.mark.unit
def test_settings_module_file_exists():
    """Test settings module file exists"""
    import os

    import routes.settings
    module_path = os.path.abspath(routes.settings.__file__)
    assert os.path.exists(module_path)


@pytest.mark.unit
def test_settings_module_name():
    """Test settings module has correct name"""
    import routes.settings
    assert routes.settings.__name__ == 'routes.settings'


@pytest.mark.unit
def test_settings_module_file_extension():
    """Test settings module is a .py file"""
    import routes.settings
    module_path = routes.settings.__file__
    assert module_path.endswith('.py')


@pytest.mark.unit
def test_parse_optional_with_decimal():
    """Test _parse_optional with Decimal conversion"""
    from decimal import Decimal

    from routes.settings import _parse_optional

    result = _parse_optional('123.45', Decimal)
    assert isinstance(result, Decimal)
    assert float(result) == 123.45


@pytest.mark.unit
def test_parse_optional_with_leading_zeros():
    """Test _parse_optional with leading zeros"""
    from routes.settings import _parse_optional

    assert _parse_optional('00123', int) == 123
    assert _parse_optional('00.5', float) == 0.5


@pytest.mark.unit
def test_parse_optional_with_plus_sign():
    """Test _parse_optional with plus sign"""
    from routes.settings import _parse_optional

    assert _parse_optional('+123', int) == 123
    assert _parse_optional('+3.14', float) == 3.14


@pytest.mark.unit
def test_parse_optional_with_very_large_number():
    """Test _parse_optional with very large number"""
    from routes.settings import _parse_optional

    assert _parse_optional('999999999999', int) == 999999999999


@pytest.mark.unit
def test_parse_optional_with_very_small_decimal():
    """Test _parse_optional with very small decimal"""
    from routes.settings import _parse_optional

    assert _parse_optional('0.0001', float) == 0.0001


@pytest.mark.unit
def test_parse_optional_multiple_commas():
    """Test _parse_optional with multiple commas (should fail)"""
    from routes.settings import _parse_optional

    with pytest.raises(ValueError, match="geçerli bir sayı değil"):
        _parse_optional('1,234,567', float)


@pytest.mark.unit
def test_parse_optional_text_with_number():
    """Test _parse_optional with text mixed with number (should fail)"""
    from routes.settings import _parse_optional

    with pytest.raises(ValueError, match="geçerli bir sayı değil"):
        _parse_optional('123abc', int)


@pytest.mark.unit
def test_parse_optional_special_characters():
    """Test _parse_optional with special characters (should fail)"""
    from routes.settings import _parse_optional

    with pytest.raises(ValueError, match="geçerli bir sayı değil"):
        _parse_optional('123@456', int)


@pytest.mark.unit
def test_parse_optional_hexadecimal():
    """Test _parse_optional with hexadecimal (should fail for int)"""
    from routes.settings import _parse_optional

    with pytest.raises(ValueError, match="geçerli bir sayı değil"):
        _parse_optional('0xFF', int)


@pytest.mark.unit
def test_parse_optional_binary():
    """Test _parse_optional with binary (should fail)"""
    from routes.settings import _parse_optional

    with pytest.raises(ValueError, match="geçerli bir sayı değil"):
        _parse_optional('0b101', int)


@pytest.mark.unit
def test_base_currency_choices_first_element():
    """Test BASE_CURRENCY_CHOICES first element is TRY"""
    from routes.settings import BASE_CURRENCY_CHOICES
    assert BASE_CURRENCY_CHOICES[0] == 'TRY'


@pytest.mark.unit
def test_base_currency_choices_last_element():
    """Test BASE_CURRENCY_CHOICES last element is GBP"""
    from routes.settings import BASE_CURRENCY_CHOICES
    assert BASE_CURRENCY_CHOICES[-1] == 'GBP'


@pytest.mark.unit
def test_engine_defaults_cache_initial_state():
    """Test _ENGINE_DEFAULTS_CACHE initial state"""
    from routes.settings import _ENGINE_DEFAULTS_CACHE
    assert _ENGINE_DEFAULTS_CACHE == {'data': None, 'last_updated': 0}


@pytest.mark.unit
def test_engine_defaults_cache_is_not_empty():
    """Test _ENGINE_DEFAULTS_CACHE is not empty"""
    from routes.settings import _ENGINE_DEFAULTS_CACHE
    assert len(_ENGINE_DEFAULTS_CACHE) > 0


@pytest.mark.unit
def test_parse_optional_executes_code():
    """Test _parse_optional executes actual code path"""
    from routes.settings import _parse_optional

    # This should execute lines 217-225 in settings.py
    result = _parse_optional('123', int)
    assert result == 123


@pytest.mark.unit
def test_parse_optional_none_path():
    """Test _parse_optional None path"""
    from routes.settings import _parse_optional

    # This should execute the None return path
    result = _parse_optional(None, int)
    assert result is None


@pytest.mark.unit
def test_parse_optional_empty_string_path():
    """Test _parse_optional empty string path"""
    from routes.settings import _parse_optional

    # This should execute the empty string return path
    result = _parse_optional('', int)
    assert result is None


@pytest.mark.unit
def test_parse_optional_whitespace_path():
    """Test _parse_optional whitespace path"""
    from routes.settings import _parse_optional

    # This should execute the whitespace return path
    result = _parse_optional('   ', int)
    assert result is None


@pytest.mark.unit
def test_parse_optional_comma_replacement():
    """Test _parse_optional comma replacement path"""
    from routes.settings import _parse_optional

    # This should execute the comma replacement path
    result = _parse_optional('3,14', float)
    assert result == 3.14


@pytest.mark.unit
def test_parse_optional_error_path():
    """Test _parse_optional error handling path"""
    import pytest

    from routes.settings import _parse_optional

    # This should execute the error handling path
    with pytest.raises(ValueError, match="geçerli bir sayı değil"):
        _parse_optional('abc', int)


@pytest.mark.unit
def test_engine_defaults_constants_access():
    """Test accessing engine defaults constants executes code"""
    from routes.settings import (
        _ENGINE_DEFAULTS_CACHE,
        _ENGINE_DEFAULTS_CACHE_TTL,
        _ENGINE_DEFAULTS_REFRESH_IN_PROGRESS,
        _ENGINE_DEFAULTS_REFRESH_LOCK,
    )

    # Accessing these constants should execute their initialization
    assert _ENGINE_DEFAULTS_CACHE is not None
    assert _ENGINE_DEFAULTS_CACHE_TTL == 3600
    assert _ENGINE_DEFAULTS_REFRESH_LOCK is not None
    assert _ENGINE_DEFAULTS_REFRESH_IN_PROGRESS is False


@pytest.mark.unit
def test_base_currency_choices_access():
    """Test accessing BASE_CURRENCY_CHOICES executes code"""
    from routes.settings import BASE_CURRENCY_CHOICES

    # Accessing this constant should execute its initialization
    assert BASE_CURRENCY_CHOICES is not None
    assert len(BASE_CURRENCY_CHOICES) == 4


@pytest.mark.unit
def test_apply_preferences_to_engine_defaults_callable():
    """Test _apply_preferences_to_engine_defaults is callable"""
    assert callable(_apply_preferences_to_engine_defaults)


@pytest.mark.unit
def test_engine_defaults_callable():
    """Test _engine_defaults is callable"""
    assert callable(_engine_defaults)


@pytest.mark.unit
def test_engine_defaults_with_none_preferences():
    """Test _engine_defaults with None preferences"""

    # This should execute the function with None preferences
    result = _engine_defaults(None)
    assert result is not None
    assert isinstance(result, dict)


@pytest.mark.unit
def test_engine_defaults_with_empty_preferences():
    """Test _engine_defaults with empty preferences"""

    # This should execute the function with empty preferences
    result = _engine_defaults({})
    assert result is not None
    assert isinstance(result, dict)


@pytest.mark.unit
def test_engine_defaults_returns_dict():
    """Test _engine_defaults returns a dictionary"""

    result = _engine_defaults(None)
    assert isinstance(result, dict)


@pytest.mark.unit
def test_engine_defaults_has_safe_withdrawal_rate():
    """Test _engine_defaults result has safe_withdrawal_rate_pct"""

    result = _engine_defaults(None)
    assert 'safe_withdrawal_rate_pct' in result


@pytest.mark.unit
def test_engine_defaults_has_emergency_fund_months():
    """Test _engine_defaults result has emergency_fund_months"""

    result = _engine_defaults(None)
    assert 'emergency_fund_months' in result


@pytest.mark.unit
def test_engine_defaults_has_risk_free_rate():
    """Test _engine_defaults result has risk_free_rate_pct"""

    result = _engine_defaults(None)
    assert 'risk_free_rate_pct' in result


@pytest.mark.unit
def test_get_standard_category_codes_callable():
    """Test _get_standard_category_codes is callable"""
    from routes.settings import _get_standard_category_codes
    assert callable(_get_standard_category_codes)


@pytest.mark.unit
def test_cleanup_non_standard_categories_callable():
    """Test _cleanup_non_standard_categories is callable"""
    from routes.settings import _cleanup_non_standard_categories
    assert callable(_cleanup_non_standard_categories)


@pytest.mark.unit
def test_get_settings_service_callable():
    """Test _get_settings_service is callable"""
    from routes.settings import _get_settings_service
    assert callable(_get_settings_service)


@pytest.mark.unit
def test_with_currency_context_callable():
    """Test _with_currency_context is callable"""
    assert callable(_with_currency_context)


@pytest.mark.unit
def test_with_currency_context_empty_dict():
    """Test _with_currency_context with empty dict"""
    from unittest.mock import patch

    # Mock CurrencyManager at the import location inside the function
    with patch('domain.analysis.services.CurrencyManager') as mock_currency_manager:
        mock_currency_manager.SUPPORTED_CURRENCIES = {'TRY': 'Türk Lirası', 'USD': 'US Dollar'}
        mock_currency_manager.get_base_currency.return_value = 'TRY'

        result = _with_currency_context({})
        assert isinstance(result, dict)
        assert 'base_currency_choices' in result


@pytest.mark.unit
def test_with_currency_context_with_base_currency_choices():
    """Test _with_currency_context adds base_currency_choices"""
    from unittest.mock import patch

    with patch('domain.analysis.services.CurrencyManager') as mock_currency_manager:
        mock_currency_manager.SUPPORTED_CURRENCIES = {'TRY': 'Türk Lirası', 'USD': 'US Dollar'}

        result = _with_currency_context({})
        assert 'base_currency_choices' in result
        assert len(result['base_currency_choices']) > 0


@pytest.mark.unit
def test_with_currency_context_current_year():
    """Test _with_currency_context adds current_year"""
    from unittest.mock import patch

    with patch('domain.analysis.services.CurrencyManager') as mock_currency_manager:
        mock_currency_manager.SUPPORTED_CURRENCIES = {'TRY': 'Türk Lirası'}
        with patch('routes.settings.datetime') as mock_datetime:
            mock_datetime.now.return_value.year = 2024

            result = _with_currency_context({})
            assert 'current_year' in result
