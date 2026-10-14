"""
Unit Tests - Assets Routes
Asset route functions
"""

from unittest.mock import Mock, patch

import pytest

from routes.assets import (
    _dispatch_portfolio_event,
    _get_outbox,
    _get_portfolio_app_service,
    _redirect_after_asset_action,
    _wants_json_response,
    register_asset_routes,
)


@pytest.mark.unit
def test_get_portfolio_app_service():
    """Test _get_portfolio_app_service function"""
    with patch('bootstrap.get_container') as mock_get_container:
        mock_container = Mock()
        mock_applications = Mock()
        mock_portfolio = Mock()
        mock_applications.portfolio.return_value = mock_portfolio
        mock_container.applications = mock_applications
        mock_get_container.return_value = mock_container

        result = _get_portfolio_app_service()
        assert result == mock_portfolio


@pytest.mark.unit
def test_get_outbox():
    """Test _get_outbox function"""
    with patch('bootstrap.get_container') as mock_get_container:
        mock_container = Mock()
        mock_infrastructure = Mock()
        mock_outbox = Mock()
        mock_infrastructure.outbox.return_value = mock_outbox
        mock_container.infrastructure = mock_infrastructure
        mock_get_container.return_value = mock_container

        result = _get_outbox()
        assert result == mock_outbox


@pytest.mark.unit
def test_dispatch_portfolio_event():
    """Test _dispatch_portfolio_event function"""
    mock_event = Mock()

    with patch('routes.assets._get_outbox') as mock_get_outbox:
        mock_outbox = Mock()
        mock_get_outbox.return_value = mock_outbox

        _dispatch_portfolio_event(mock_event)

        mock_outbox.save.assert_called_once_with(mock_event)




@pytest.mark.unit
def test_register_asset_routes():
    """Test register_asset_routes function"""
    mock_bp = Mock()
    mock_bp.route = Mock(return_value=lambda f: f)

    with patch('routes.assets._get_portfolio_app_service') as mock_get_service:
        mock_service = Mock()
        mock_get_service.return_value = mock_service

        register_asset_routes(mock_bp)

        assert mock_bp.route.called


@pytest.mark.unit
def test_assets_imports():
    """Test that assets functions can be imported"""
    from routes.assets import (
        _dispatch_portfolio_event,
        _get_outbox,
        _get_portfolio_app_service,
        register_asset_routes,
    )

    assert callable(_get_portfolio_app_service)
    assert callable(_get_outbox)
    assert callable(_dispatch_portfolio_event)
    assert callable(_wants_json_response)
    assert callable(_redirect_after_asset_action)
    assert callable(register_asset_routes)


@pytest.mark.unit
def test_assets_routes_structure():
    """Test assets routes module structure"""
    import routes.assets as assets_module

    # Check for expected functions
    assert hasattr(assets_module, '_get_portfolio_app_service')
    assert hasattr(assets_module, '_get_outbox')
    assert hasattr(assets_module, '_dispatch_portfolio_event')
    assert hasattr(assets_module, '_wants_json_response')
    assert hasattr(assets_module, '_redirect_after_asset_action')
    assert hasattr(assets_module, 'register_asset_routes')

    # Check for expected imports
    assert hasattr(assets_module, 'logging')
    assert hasattr(assets_module, 'flash')
    assert hasattr(assets_module, 'g')
    assert hasattr(assets_module, 'jsonify')
    assert hasattr(assets_module, 'redirect')
    assert hasattr(assets_module, 'render_template')
    assert hasattr(assets_module, 'request')
    assert hasattr(assets_module, 'session')
    assert hasattr(assets_module, 'url_for')


@pytest.mark.unit
def test_assets_logger_exists():
    """Test assets module has logger"""
    import routes.assets as assets_module
    assert hasattr(assets_module, 'logger')
    assert assets_module.logger is not None


@pytest.mark.unit
def test_register_asset_routes_route_registration():
    """Test register_asset_routes registers routes"""
    mock_bp = Mock()
    mock_bp.route = Mock(return_value=lambda f: f)

    with patch('routes.assets._get_portfolio_app_service') as mock_get_service:
        mock_service = Mock()
        mock_get_service.return_value = mock_service

        register_asset_routes(mock_bp)

        # Should register multiple routes
        assert mock_bp.route.call_count >= 8


@pytest.mark.unit
def test_assets_module_has_required_imports():
    """Test assets module has required imports"""
    import routes.assets as assets_module

    # Flask imports
    assert hasattr(assets_module, 'flash')
    assert hasattr(assets_module, 'g')
    assert hasattr(assets_module, 'jsonify')
    assert hasattr(assets_module, 'redirect')
    assert hasattr(assets_module, 'render_template')
    assert hasattr(assets_module, 'request')
    assert hasattr(assets_module, 'session')
    assert hasattr(assets_module, 'url_for')

    # Custom imports
    assert hasattr(assets_module, 'get_container')
    assert hasattr(assets_module, 'AssetAddedEvent')
    assert hasattr(assets_module, 'AssetRemovedEvent')
    assert hasattr(assets_module, 'AssetUpdatedEvent')
    assert hasattr(assets_module, 'LedgerError')
    assert hasattr(assets_module, 'create_asset_position')
    assert hasattr(assets_module, 'delete_asset_position')
    assert hasattr(assets_module, 'parse_asset_payload')
    assert hasattr(assets_module, 'sell_asset_position')
    assert hasattr(assets_module, 'update_asset_valuation')
    assert hasattr(assets_module, 'today_display')
    assert hasattr(assets_module, 'to_decimal')
    assert hasattr(assets_module, 'handle_ajax_or_flash')
    assert hasattr(assets_module, 'is_ajax_request')
    assert hasattr(assets_module, 'rollback_session')


@pytest.mark.unit
def test_assets_blueprint_parameter():
    """Test register_asset_routes accepts blueprint parameter"""
    mock_bp = Mock()
    mock_bp.route = Mock(return_value=lambda f: f)

    with patch('routes.assets._get_portfolio_app_service') as mock_get_service:
        mock_service = Mock()
        mock_get_service.return_value = mock_service

        # Should not raise exception
        register_asset_routes(mock_bp)


@pytest.mark.unit
def test_assets_route_exists():
    """Test assets route exists"""
    import inspect

    import routes.assets as assets_module

    source = inspect.getsource(assets_module)
    assert '/assets' in source


@pytest.mark.unit
def test_investment_performance_route_exists():
    """Test investment performance route exists"""
    import inspect

    import routes.assets as assets_module

    source = inspect.getsource(assets_module)
    assert '/investment_performance' in source


@pytest.mark.unit
def test_assets_view_route_exists():
    """Test assets view route exists"""
    import inspect

    import routes.assets as assets_module

    source = inspect.getsource(assets_module)
    assert '/assets_view' in source


@pytest.mark.unit
def test_assets_management_route_exists():
    """Test assets management route exists"""
    import inspect

    import routes.assets as assets_module

    source = inspect.getsource(assets_module)
    assert '/assets_management' in source


@pytest.mark.unit
def test_new_asset_route_exists():
    """Test new asset route exists"""
    import inspect

    import routes.assets as assets_module

    source = inspect.getsource(assets_module)
    assert '/new_asset' in source


@pytest.mark.unit
def test_update_asset_route_exists():
    """Test update asset route exists"""
    import inspect

    import routes.assets as assets_module

    source = inspect.getsource(assets_module)
    assert '/update_asset' in source


@pytest.mark.unit
def test_edit_asset_route_exists():
    """Test edit asset route exists"""
    import inspect

    import routes.assets as assets_module

    source = inspect.getsource(assets_module)
    assert '/edit_asset' in source


@pytest.mark.unit
def test_delete_asset_route_exists():
    """Test delete asset route exists"""
    import inspect

    import routes.assets as assets_module

    source = inspect.getsource(assets_module)
    assert '/delete_asset' in source


@pytest.mark.unit
def test_sell_asset_route_exists():
    """Test sell asset route exists"""
    import inspect

    import routes.assets as assets_module

    source = inspect.getsource(assets_module)
    assert '/sell_asset' in source


@pytest.mark.unit
def test_assets_error_handling_structure():
    """Test assets routes have error handling"""
    import inspect

    import routes.assets as assets_module

    # Check that the module has error handling patterns
    source = inspect.getsource(assets_module)
    assert 'except Exception' in source or 'try:' in source


@pytest.mark.unit
def test_assets_ajax_handling():
    """Test assets routes use AJAX helpers"""
    import inspect

    import routes.assets as assets_module

    source = inspect.getsource(assets_module)
    assert 'is_ajax_request' in source or 'handle_ajax_or_flash' in source


@pytest.mark.unit
def test_assets_json_responses():
    """Test assets routes use jsonify"""
    import inspect

    import routes.assets as assets_module

    source = inspect.getsource(assets_module)
    assert 'jsonify' in source


@pytest.mark.unit
def test_assets_flash_messaging():
    """Test assets routes use flash messaging"""
    import inspect

    import routes.assets as assets_module

    source = inspect.getsource(assets_module)
    assert 'flash' in source


@pytest.mark.unit
def test_assets_rollback_session():
    """Test assets routes use rollback_session"""
    import inspect

    import routes.assets as assets_module

    source = inspect.getsource(assets_module)
    assert 'rollback_session' in source


@pytest.mark.unit
def test_assets_ledger_error():
    """Test assets routes handle LedgerError"""
    import inspect

    import routes.assets as assets_module

    source = inspect.getsource(assets_module)
    assert 'LedgerError' in source


@pytest.mark.unit
def test_assets_portfolio_events():
    """Test assets routes use portfolio events"""
    import inspect

    import routes.assets as assets_module

    source = inspect.getsource(assets_module)
    assert 'AssetAddedEvent' in source or 'AssetRemovedEvent' in source or 'AssetUpdatedEvent' in source


@pytest.mark.unit
def test_assets_outbox_usage():
    """Test assets routes use outbox"""
    import inspect

    import routes.assets as assets_module

    source = inspect.getsource(assets_module)
    assert 'outbox' in source


@pytest.mark.unit
def test_assets_decimal_precision():
    """Test assets routes use decimal precision"""
    import inspect

    import routes.assets as assets_module

    source = inspect.getsource(assets_module)
    assert 'to_decimal' in source


@pytest.mark.unit
def test_assets_tenant_context():
    """Test assets routes use tenant context"""
    import inspect

    import routes.assets as assets_module

    source = inspect.getsource(assets_module)
    assert 'tenant_id' in source


@pytest.mark.unit
def test_assets_portfolio_api_endpoints():
    """Test assets routes include JSON API endpoints and cache invalidation"""
    import inspect

    import routes.assets as assets_module

    source = inspect.getsource(assets_module)
    assert '/api/portfolio/summary' in source
    assert '/api/portfolio/assets' in source
    assert 'invalidate_financial_cache' in source
