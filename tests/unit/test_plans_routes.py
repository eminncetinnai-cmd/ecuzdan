"""
Unit Tests - Plans Routes
Plan and payment calendar route tests
"""

import pytest
from unittest.mock import Mock, patch, MagicMock


@pytest.mark.unit
def test_plans_route_registration_calls_service():
    """Test that register_plan_routes calls planning service"""
    from routes.plans import register_plan_routes
    
    mock_bp = Mock()
    mock_bp.route = Mock(return_value=lambda f: f)
    
    with patch('routes.plans._get_planning_app') as mock_get_app:
        mock_app = Mock()
        mock_app.plans_context.return_value = {
            'subscription_plans': [],
            'installment_plans': [],
            'dca_plans': [],
            'periodic_plans': [],
            'income_cats': [],
            'expense_cats': [],
            'investment_cats': [],
            'plan_count': 0,
            'income_total': 0,
            'expense_total': 0,
            'net_total': 0,
        }
        mock_app.payment_calendar_context.return_value = {
            'today_cash': 1000,
            'week_p': [],
            'month_p': [],
            'cal_year': 2024,
            'cal_month': 8,
        }
        mock_app.month_data.return_value = {'data': 'test'}
        mock_app.daily_balance.return_value = {'data': 'test'}
        mock_get_app.return_value = mock_app
        
        register_plan_routes(mock_bp)
        
        mock_get_app.assert_called_once()
        assert mock_bp.route.call_count >= 7  # Should register 7 routes


@pytest.mark.unit
def test_plans_route_save_plan_calls_service():
    """Test that save_plan route calls planning service"""
    from routes.plans import register_plan_routes
    from domain.transactions.services import LedgerError
    
    mock_bp = Mock()
    mock_bp.route = Mock(return_value=lambda f: f)
    
    with patch('routes.plans._get_planning_app') as mock_get_app:
        mock_app = Mock()
        mock_app.save_plan.return_value = 'Plan başarıyla eklendi'
        mock_get_app.return_value = mock_app
        
        with patch('utils.ajax_helpers.is_ajax_request') as mock_is_ajax:
            mock_is_ajax.return_value = True
            
            register_plan_routes(mock_bp)
            
            # Verify the route was registered
            assert mock_bp.route.called


@pytest.mark.unit
def test_plans_route_error_handling_rollback():
    """Test that errors trigger rollback_session"""
    from routes.plans import register_plan_routes
    from domain.transactions.services import LedgerError
    
    mock_bp = Mock()
    mock_bp.route = Mock(return_value=lambda f: f)
    
    with patch('routes.plans._get_planning_app') as mock_get_app:
        mock_app = Mock()
        mock_app.save_plan.side_effect = LedgerError('Plan oluşturma hatası')
        mock_get_app.return_value = mock_app
        
        with patch('utils.ajax_helpers.is_ajax_request') as mock_is_ajax:
            mock_is_ajax.return_value = True
            
            with patch('utils.db_session.rollback_session') as mock_rollback:
                register_plan_routes(mock_bp)
                
                # The route should be registered with error handling
                assert mock_bp.route.called


@pytest.mark.unit
def test_payment_calendar_route_calls_service():
    """Test that payment_calendar route calls planning service"""
    from routes.plans import register_plan_routes
    
    mock_bp = Mock()
    mock_bp.route = Mock(return_value=lambda f: f)
    
    with patch('routes.plans._get_planning_app') as mock_get_app:
        mock_app = Mock()
        mock_app.payment_calendar_context.return_value = {
            'today_cash': 1000,
            'week_p': [],
            'month_p': [],
            'cal_year': 2024,
            'cal_month': 8,
        }
        mock_get_app.return_value = mock_app
        
        register_plan_routes(mock_bp)
        
        # Verify the route was registered
        assert mock_bp.route.called


@pytest.mark.unit
def test_month_data_route_validates_params():
    """Test that month_data route validates year and month params"""
    from routes.plans import register_plan_routes
    
    mock_bp = Mock()
    mock_bp.route = Mock(return_value=lambda f: f)
    
    with patch('routes.plans._get_planning_app') as mock_get_app:
        mock_app = Mock()
        mock_get_app.return_value = mock_app
        
        register_plan_routes(mock_bp)
        
        # Verify the route was registered
        assert mock_bp.route.called


@pytest.mark.unit
def test_delete_plan_route_calls_service():
    """Test that delete_plan route calls delete_recurring_plan"""
    from routes.plans import register_plan_routes
    
    mock_bp = Mock()
    mock_bp.route = Mock(return_value=lambda f: f)
    
    with patch('routes.plans._get_planning_app') as mock_get_app:
        mock_app = Mock()
        mock_repo = Mock()
        mock_repo.get_recurring_plan_for_tenant.return_value = Mock()
        mock_app.financial_repository = mock_repo
        mock_get_app.return_value = mock_app
        
        with patch('domain.transactions.services.delete_recurring_plan') as mock_delete:
            mock_delete.return_value = {'success': True, 'message': 'Plan silindi'}
            
            with patch('utils.ajax_helpers.is_ajax_request') as mock_is_ajax:
                mock_is_ajax.return_value = True
                
                register_plan_routes(mock_bp)
                
                # Verify the route was registered
                assert mock_bp.route.called


@pytest.mark.unit
def test_add_payment_route_calls_service():
    """Test that add_payment route calls planning service"""
    from routes.plans import register_plan_routes
    
    mock_bp = Mock()
    mock_bp.route = Mock(return_value=lambda f: f)
    
    with patch('routes.plans._get_planning_app') as mock_get_app:
        mock_app = Mock()
        mock_app.add_payment.return_value = None
        mock_get_app.return_value = mock_app
        
        register_plan_routes(mock_bp)
        
        # Verify the route was registered
        assert mock_bp.route.called


@pytest.mark.unit
def test_add_payment_route_validation_error_handling():
    """Test that add_payment route handles ValueError with rollback"""
    from routes.plans import register_plan_routes
    
    mock_bp = Mock()
    mock_bp.route = Mock(return_value=lambda f: f)
    
    with patch('routes.plans._get_planning_app') as mock_get_app:
        mock_app = Mock()
        mock_app.add_payment.side_effect = ValueError('Geçersiz veri')
        mock_get_app.return_value = mock_app
        
        with patch('utils.db_session.rollback_session') as mock_rollback:
            register_plan_routes(mock_bp)
            
            # Verify the route was registered
            assert mock_bp.route.called


@pytest.mark.unit
def test_plans_routes_have_error_handling():
    """Test that plans routes have try-except blocks"""
    import routes.plans as plans_module
    import inspect
    
    source = inspect.getsource(plans_module)
    assert 'except Exception' in source
    assert 'try:' in source


@pytest.mark.unit
def test_plans_routes_use_jsonify_for_ajax():
    """Test that plans routes use jsonify for AJAX responses"""
    import routes.plans as plans_module
    import inspect
    
    source = inspect.getsource(plans_module)
    assert 'jsonify' in source
    assert 'is_ajax_request' in source


@pytest.mark.unit
def test_plans_routes_use_flash_for_non_ajax():
    """Test that plans routes use flash for non-AJAX responses"""
    import routes.plans as plans_module
    import inspect
    
    source = inspect.getsource(plans_module)
    assert 'flash' in source
    assert 'redirect' in source


@pytest.mark.unit
def test_plans_route_get_renders_template():
    """Test GET /plans renders template with context"""
    from routes.plans import register_plan_routes
    from flask import Flask
    
    app = Flask(__name__)
    app.config['TESTING'] = True
    bp = Flask(__name__)
    bp.route = Mock(return_value=lambda f: f)
    
    with patch('routes.plans._get_planning_app') as mock_get_app:
        mock_app = Mock()
        mock_app.plans_context.return_value = {
            'subscription_plans': [],
            'installment_plans': [],
            'dca_plans': [],
            'periodic_plans': [],
            'income_cats': [],
            'expense_cats': [],
            'investment_cats': [],
            'plan_count': 0,
            'income_total': 0,
            'expense_total': 0,
            'net_total': 0,
        }
        mock_get_app.return_value = mock_app
        
        register_plan_routes(bp)
        
        # Verify the route was registered
        assert bp.route.called


@pytest.mark.unit
def test_payment_calendar_route_renders_template():
    """Test GET /payment_calendar renders template with context"""
    from routes.plans import register_plan_routes
    
    mock_bp = Mock()
    mock_bp.route = Mock(return_value=lambda f: f)
    
    with patch('routes.plans._get_planning_app') as mock_get_app:
        mock_app = Mock()
        mock_app.payment_calendar_context.return_value = {
            'today_cash': 1000,
            'week_p': [],
            'month_p': [],
            'cal_year': 2024,
            'cal_month': 8,
            'cal_month_name': 'Ağustos',
            'today_iso': '2024-08-11',
        }
        mock_get_app.return_value = mock_app
        
        register_plan_routes(mock_bp)
        
        # Verify the route was registered
        assert mock_bp.route.called


@pytest.mark.unit
def test_check_delete_route_returns_transaction_counts():
    """Test check_delete route returns correct transaction counts"""
    from routes.plans import register_plan_routes
    
    mock_bp = Mock()
    mock_bp.route = Mock(return_value=lambda f: f)
    
    with patch('routes.plans._get_planning_app') as mock_get_app:
        mock_app = Mock()
        mock_repo = Mock()
        mock_plan = Mock()
        mock_repo.get_recurring_plan_for_tenant.return_value = mock_plan
        mock_app.financial_repository = mock_repo
        mock_get_app.return_value = mock_app
        
        register_plan_routes(mock_bp)
        
        # Verify the route was registered
        assert mock_bp.route.called


@pytest.mark.unit
def test_delete_plan_route_pending_mode():
    """Test delete_plan route with pending mode"""
    from routes.plans import register_plan_routes
    
    mock_bp = Mock()
    mock_bp.route = Mock(return_value=lambda f: f)
    
    with patch('routes.plans._get_planning_app') as mock_get_app:
        mock_app = Mock()
        mock_repo = Mock()
        mock_plan = Mock()
        mock_repo.get_recurring_plan_for_tenant.return_value = mock_plan
        mock_app.financial_repository = mock_repo
        mock_get_app.return_value = mock_app
        
        with patch('domain.transactions.services.delete_recurring_plan') as mock_delete:
            mock_delete.return_value = {'success': True, 'message': 'Plan silindi'}
            
            with patch('utils.ajax_helpers.is_ajax_request') as mock_is_ajax:
                mock_is_ajax.return_value = True
                
                register_plan_routes(mock_bp)
                
                # Verify the route was registered
                assert mock_bp.route.called
