"""
Unit Tests - I18n
Internationalization module tests
"""

import pytest
import json
import os
from unittest.mock import Mock, patch, MagicMock


@pytest.mark.unit
def test_i18n_module_imports():
    """Test i18n module can be imported"""
    from infrastructure.i18n import I18n, i18n
    assert I18n is not None
    assert i18n is not None


@pytest.mark.unit
def test_i18n_module_structure():
    """Test i18n module structure"""
    import infrastructure.i18n as i18n_module
    
    # Check for expected class and instance
    assert hasattr(i18n_module, 'I18n')
    assert hasattr(i18n_module, 'i18n')


@pytest.mark.unit
def test_i18n_class_init_without_app():
    """Test I18n initialization without app"""
    from infrastructure.i18n import I18n
    
    i18n = I18n()
    assert i18n.app is None
    assert i18n.translations == {}
    assert i18n.default_lang == 'tr'


@pytest.mark.unit
def test_i18n_class_init_with_app():
    """Test I18n initialization with app - skipped due to Flask context requirement"""
    pytest.skip("Requires Flask application context")


@pytest.mark.unit
def test_i18n_init_app():
    """Test I18n init_app method - skipped due to Flask context requirement"""
    pytest.skip("Requires Flask application context")


@pytest.mark.unit
def test_i18n_load_translations():
    """Test I18n load_translations method"""
    from infrastructure.i18n import I18n
    
    i18n = I18n()
    i18n.translation_folder = '/fake/folder'
    
    with patch('os.listdir') as mock_listdir:
        mock_listdir.return_value = ['tr.json', 'en.json']
        
        with patch('builtins.open', create=True) as mock_open:
            mock_file = MagicMock()
            mock_file.__enter__ = Mock(return_value=mock_file)
            mock_file.__exit__ = Mock(return_value=False)
            mock_file.read.return_value = '{"test": "test_value"}'
            mock_open.return_value = mock_file
            
            with patch('json.load') as mock_json_load:
                mock_json_load.return_value = {'test': 'test_value'}
                
                i18n.load_translations()
                
                assert 'tr' in i18n.translations
                assert 'en' in i18n.translations


@pytest.mark.unit
def test_i18n_load_translations_no_json_files():
    """Test I18n load_translations with no JSON files"""
    from infrastructure.i18n import I18n
    
    i18n = I18n()
    i18n.translation_folder = '/fake/folder'
    
    with patch('os.listdir') as mock_listdir:
        mock_listdir.return_value = ['readme.txt', 'config.yaml']
        
        i18n.load_translations()
        
        assert i18n.translations == {}


@pytest.mark.unit
def test_i18n_get_locale_from_session():
    """Test I18n get_locale from session"""
    from infrastructure.i18n import I18n
    
    i18n = I18n()
    i18n.translations = {'tr': {}, 'en': {}}
    
    mock_session = {'lang': 'en'}
    mock_request = Mock()
    mock_request.accept_languages.best_match = Mock(return_value=None)
    
    with patch('infrastructure.i18n.session', mock_session):
        with patch('infrastructure.i18n.request', mock_request):
            result = i18n.get_locale()
            assert result == 'en'


@pytest.mark.unit
def test_i18n_get_locale_from_user():
    """Test I18n get_locale from user - skipped due to complex models mocking"""
    pytest.skip("Requires complex models mocking")


@pytest.mark.unit
def test_i18n_get_locale_from_browser():
    """Test I18n get_locale from browser"""
    from infrastructure.i18n import I18n
    
    i18n = I18n()
    i18n.translations = {'tr': {}, 'en': {}}
    
    mock_session = {}
    mock_request = Mock()
    mock_request.accept_languages.best_match = Mock(return_value='en')
    
    with patch('infrastructure.i18n.session', mock_session):
        with patch('infrastructure.i18n.request', mock_request):
            result = i18n.get_locale()
            assert result == 'en'


@pytest.mark.unit
def test_i18n_get_locale_default():
    """Test I18n get_locale returns default"""
    from infrastructure.i18n import I18n
    
    i18n = I18n()
    i18n.translations = {'tr': {}, 'en': {}}
    
    mock_session = {}
    mock_request = Mock()
    mock_request.accept_languages.best_match = Mock(return_value=None)
    
    with patch('infrastructure.i18n.session', mock_session):
        with patch('infrastructure.i18n.request', mock_request):
            result = i18n.get_locale()
            assert result == 'tr'


@pytest.mark.unit
def test_i18n_before_request():
    """Test I18n before_request method"""
    from infrastructure.i18n import I18n
    
    i18n = I18n()
    i18n.translations = {'tr': {}, 'en': {}}
    
    mock_session = {}
    mock_g = Mock()
    mock_request = Mock()
    mock_request.accept_languages.best_match = Mock(return_value=None)
    
    with patch('infrastructure.i18n.session', mock_session):
        with patch('infrastructure.i18n.request', mock_request):
            with patch('infrastructure.i18n.g', mock_g):
                i18n.before_request()
                assert mock_g.lang == 'tr'
                assert mock_session['lang'] == 'tr'


@pytest.mark.unit
def test_i18n_gettext():
    """Test I18n gettext method"""
    from infrastructure.i18n import I18n
    
    i18n = I18n()
    i18n.translations = {'tr': {'hello': 'Merhaba'}, 'en': {'hello': 'Hello'}}
    
    mock_g = Mock()
    mock_g.get = Mock(return_value='tr')
    
    with patch('infrastructure.i18n.g', mock_g):
        result = i18n.gettext('hello')
        assert result == 'Merhaba'


@pytest.mark.unit
def test_i18n_gettext_with_variables():
    """Test I18n gettext with variables"""
    from infrastructure.i18n import I18n
    
    i18n = I18n()
    i18n.translations = {'tr': {'welcome': 'Hoş geldin {name}'}, 'en': {'welcome': 'Welcome {name}'}}
    
    mock_g = Mock()
    mock_g.get = Mock(return_value='tr')
    
    with patch('infrastructure.i18n.g', mock_g):
        result = i18n.gettext('welcome', name='John')
        assert result == 'Hoş geldin John'


@pytest.mark.unit
def test_i18n_gettext_fallback_to_default():
    """Test I18n gettext fallback to default language"""
    from infrastructure.i18n import I18n
    
    i18n = I18n()
    i18n.translations = {'tr': {'hello': 'Merhaba'}, 'en': {}}
    
    mock_g = Mock()
    mock_g.get = Mock(return_value='en')
    
    with patch('infrastructure.i18n.g', mock_g):
        result = i18n.gettext('hello')
        assert result == 'Merhaba'


@pytest.mark.unit
def test_i18n_gettext_key_not_found():
    """Test I18n gettext when key not found"""
    from infrastructure.i18n import I18n
    
    i18n = I18n()
    i18n.translations = {'tr': {}, 'en': {}}
    
    mock_g = Mock()
    mock_g.get = Mock(return_value='tr')
    
    with patch('infrastructure.i18n.g', mock_g):
        result = i18n.gettext('missing_key')
        assert result == 'missing_key'


@pytest.mark.unit
def test_i18n_inject_gettext():
    """Test I18n inject_gettext method"""
    from infrastructure.i18n import I18n
    
    i18n = I18n()
    result = i18n.inject_gettext()
    
    assert isinstance(result, dict)
    assert '_' in result
    assert 'get_locale' in result
    assert callable(result['_'])
    assert callable(result['get_locale'])


@pytest.mark.unit
def test_i18n_global_instance():
    """Test global i18n instance"""
    from infrastructure.i18n import i18n
    
    assert i18n is not None
    assert hasattr(i18n, 'translations')
    assert hasattr(i18n, 'default_lang')


@pytest.mark.unit
def test_i18n_default_lang():
    """Test I18n default language"""
    from infrastructure.i18n import I18n
    
    i18n = I18n()
    assert i18n.default_lang == 'tr'


@pytest.mark.unit
def test_i18n_set_default_lang():
    """Test setting custom default language"""
    from infrastructure.i18n import I18n
    
    i18n = I18n()
    i18n.default_lang = 'en'
    assert i18n.default_lang == 'en'


@pytest.mark.unit
def test_i18n_translations_dict():
    """Test I18n translations dictionary"""
    from infrastructure.i18n import I18n
    
    i18n = I18n()
    i18n.translations = {'tr': {'hello': 'Merhaba'}, 'en': {'hello': 'Hello'}}
    
    assert 'tr' in i18n.translations
    assert 'en' in i18n.translations
    assert i18n.translations['tr']['hello'] == 'Merhaba'


@pytest.mark.unit
def test_i18n_gettext_missing_language():
    """Test I18n gettext when language not in translations"""
    from infrastructure.i18n import I18n
    
    i18n = I18n()
    i18n.translations = {'tr': {'hello': 'Merhaba'}}
    
    mock_g = Mock()
    mock_g.get = Mock(return_value='fr')
    
    with patch('infrastructure.i18n.g', mock_g):
        result = i18n.gettext('hello')
        assert result == 'Merhaba'  # Falls back to default


@pytest.mark.unit
def test_i18n_gettext_empty_variables():
    """Test I18n gettext with no variables when template expects them"""
    from infrastructure.i18n import I18n
    
    i18n = I18n()
    i18n.translations = {'tr': {'welcome': 'Hoş geldin {name}'}}
    
    mock_g = Mock()
    mock_g.get = Mock(return_value='tr')
    
    with patch('infrastructure.i18n.g', mock_g):
        # This should raise an error due to missing variable
        with pytest.raises(KeyError):
            i18n.gettext('welcome')


@pytest.mark.unit
def test_i18n_gettext_multiple_variables():
    """Test I18n gettext with multiple variables"""
    from infrastructure.i18n import I18n
    
    i18n = I18n()
    i18n.translations = {'tr': {'greeting': 'Merhaba {name}, bugün {day}'}}
    
    mock_g = Mock()
    mock_g.get = Mock(return_value='tr')
    
    with patch('infrastructure.i18n.g', mock_g):
        result = i18n.gettext('greeting', name='John', day='Pazartesi')
        assert result == 'Merhaba John, bugün Pazartesi'


@pytest.mark.unit
def test_i18n_gettext_no_g_lang():
    """Test I18n gettext when g.lang is not set"""
    from infrastructure.i18n import I18n
    
    i18n = I18n()
    i18n.translations = {'tr': {'hello': 'Merhaba'}, 'en': {'hello': 'Hello'}}
    
    mock_g = Mock()
    mock_g.get = Mock(return_value=None)  # g.lang not set
    
    with patch('infrastructure.i18n.g', mock_g):
        result = i18n.gettext('hello')
        assert result == 'Merhaba'  # Falls back to default


@pytest.mark.unit
def test_i18n_gettext_empty_translations():
    """Test I18n gettext with empty translations"""
    from infrastructure.i18n import I18n
    
    i18n = I18n()
    i18n.translations = {}
    
    mock_g = Mock()
    mock_g.get = Mock(return_value='tr')
    
    with patch('infrastructure.i18n.g', mock_g):
        result = i18n.gettext('hello')
        assert result == 'hello'  # Returns key as fallback


@pytest.mark.unit
def test_i18n_get_locale_session_priority():
    """Test that session has highest priority in get_locale"""
    from infrastructure.i18n import I18n
    
    i18n = I18n()
    i18n.translations = {'tr': {}, 'en': {}}
    
    # Session has lang set
    mock_session = {'lang': 'en', 'user_id': 1}
    mock_request = Mock()
    mock_request.accept_languages.best_match = Mock(return_value='tr')
    
    with patch('infrastructure.i18n.session', mock_session):
        with patch('infrastructure.i18n.request', mock_request):
            result = i18n.get_locale()
            assert result == 'en'  # Session takes priority


@pytest.mark.unit
def test_i18n_get_locale_no_session_user():
    """Test get_locale when user_id in session but no lang - skipped due to DB context"""
    pytest.skip("Requires Flask application context for database access")


@pytest.mark.unit
def test_i18n_get_locale_browser_not_in_translations():
    """Test get_locale when browser lang returns None (no match)"""
    from infrastructure.i18n import I18n
    
    i18n = I18n()
    i18n.translations = {'tr': {}, 'en': {}}
    
    mock_session = {}
    mock_request = Mock()
    mock_request.accept_languages.best_match = Mock(return_value=None)  # No match
    
    with patch('infrastructure.i18n.session', mock_session):
        with patch('infrastructure.i18n.request', mock_request):
            result = i18n.get_locale()
            assert result == 'tr'  # Falls back to default
