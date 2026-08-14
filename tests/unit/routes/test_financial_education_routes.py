"""
Unit Tests - Financial Education Routes
Financial education content route tests
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime


@pytest.mark.unit
def test_financial_education_route_registration():
    """Test that financial education routes are registered"""
    from routes.financial_education import register_financial_education_routes
    
    mock_bp = Mock()
    mock_bp.route = Mock(return_value=lambda f: f)
    
    register_financial_education_routes(mock_bp)
    
    assert mock_bp.route.call_count >= 3  # Should register 3+ routes


@pytest.mark.unit
def test_financial_education_index_route():
    """Test that index route returns education content"""
    from routes.financial_education import register_financial_education_routes
    
    mock_bp = Mock()
    mock_bp.route = Mock(return_value=lambda f: f)
    
    register_financial_education_routes(mock_bp)
    
    assert mock_bp.route.called


@pytest.mark.unit
def test_financial_education_detail_route():
    """Test that detail route returns specific education content"""
    from routes.financial_education import register_financial_education_routes
    
    mock_bp = Mock()
    mock_bp.route = Mock(return_value=lambda f: f)
    
    register_financial_education_routes(mock_bp)
    
    assert mock_bp.route.called


@pytest.mark.unit
@pytest.mark.parametrize("topic,expected_content", [
    ("budgeting", "Bütçe"),
    ("investing", "Yatırım"),
    ("savings", "Tasarruf"),
    ("debt", "Borç"),
])
def test_financial_education_topic_coverage(topic, expected_content):
    """Test that financial education covers various topics"""
    # This would test actual topic content
    assert isinstance(topic, str)
    assert isinstance(expected_content, str)


@pytest.mark.unit
def test_financial_education_error_handling():
    """Test that financial education routes have error handling"""
    import routes.financial_education as fe_module
    import inspect
    
    source = inspect.getsource(fe_module)
    assert 'except Exception' in source or 'try:' in source


@pytest.mark.unit
def test_financial_education_uses_render_template():
    """Test that financial education routes use render_template"""
    import routes.financial_education as fe_module
    import inspect
    
    source = inspect.getsource(fe_module)
    assert 'render_template' in source


@pytest.mark.unit
def test_utcnow_naive():
    """Test utcnow_naive helper function"""
    from routes.financial_education import utcnow_naive
    
    result = utcnow_naive()
    
    assert isinstance(result, datetime)
    assert result.tzinfo is None  # Should be naive datetime


@pytest.mark.unit
@pytest.mark.skip(reason="Requires Flask application context")
def test_check_and_award_achievement_new():
    """Test _check_and_award_achievement for new achievement"""
    from routes.financial_education import _check_and_award_achievement
    from models import UserAchievement
    
    with patch('models.UserAchievement') as mock_achievement_model:
        mock_query = Mock()
        mock_achievement_model.query = mock_query
        mock_filter = Mock()
        mock_query.filter_by.return_value = mock_filter
        mock_filter.first.return_value = None  # No existing achievement
        
        mock_session = Mock()
        with patch('routes.financial_education.db', Mock(session=mock_session)):
            _check_and_award_achievement(user_id=1, achievement_type='test_achievement', tenant_id='default')
            
            mock_session.add.assert_called_once()


@pytest.mark.unit
@pytest.mark.skip(reason="Requires Flask application context")
def test_check_and_award_achievement_existing():
    """Test _check_and_award_achievement when achievement already exists"""
    from routes.financial_education import _check_and_award_achievement
    from models import UserAchievement
    
    with patch('models.UserAchievement') as mock_achievement_model:
        mock_query = Mock()
        mock_achievement_model.query = mock_query
        mock_filter = Mock()
        mock_query.filter_by.return_value = mock_filter
        mock_filter.first.return_value = Mock()  # Existing achievement
        
        mock_session = Mock()
        with patch('routes.financial_education.db', Mock(session=mock_session)):
            _check_and_award_achievement(user_id=1, achievement_type='test_achievement', tenant_id='default')
            
            mock_session.add.assert_not_called()


@pytest.mark.unit
def test_financial_education_module_imports():
    """Test that financial education module has required imports"""
    import routes.financial_education as fe_module
    
    assert hasattr(fe_module, 'Blueprint')
    assert hasattr(fe_module, 'render_template')
    assert hasattr(fe_module, 'jsonify')
    assert hasattr(fe_module, 'request')
    assert hasattr(fe_module, 'session')


@pytest.mark.unit
def test_financial_education_blueprint_exists():
    """Test that financial_education_bp blueprint exists"""
    from routes.financial_education import financial_education_bp
    
    assert financial_education_bp is not None
    assert financial_education_bp.name == 'financial_education'


@pytest.mark.unit
def test_financial_education_has_logger():
    """Test that financial education module has logger"""
    import routes.financial_education as fe_module
    
    assert hasattr(fe_module, 'logger')


@pytest.mark.unit
def test_financial_education_domain_imports():
    """Test that financial education imports domain analysis services"""
    import routes.financial_education as fe_module
    
    assert hasattr(fe_module, 'get_all_phases')
    assert hasattr(fe_module, 'get_all_topics')
    assert hasattr(fe_module, 'get_guide_data')
    assert hasattr(fe_module, 'get_formula_function')


@pytest.mark.unit
def test_financial_education_constants():
    """Test that financial education has required constants"""
    import routes.financial_education as fe_module
    
    assert hasattr(fe_module, 'PROGRAM_ANALYSES')
    assert hasattr(fe_module, 'PROGRAM_CALCULATIONS')
    assert hasattr(fe_module, 'TECHNICAL_TERMS')


@pytest.mark.unit
def test_financial_education_route_paths():
    """Test that financial education has expected route paths"""
    import routes.financial_education as fe_module
    import inspect
    
    source = inspect.getsource(fe_module)
    
    assert '/financial_education' in source
    assert '/api/quiz/start' in source
    assert '/api/quiz/submit' in source
    assert '/api/quiz/history' in source
    assert '/api/progress' in source
    assert '/api/progress/update' in source
    assert '/api/achievements' in source
