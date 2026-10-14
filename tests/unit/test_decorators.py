"""
Unit Tests - Decorators
Common decorators for route protection and authentication tests
"""

from unittest.mock import Mock, patch

import pytest

from utils.decorators import login_required


@pytest.mark.unit
def test_decorators_module_imports():
    """Test decorators module can be imported"""
    assert login_required is not None


@pytest.mark.unit
def test_decorators_module_structure():
    """Test decorators module structure"""
    import utils.decorators as decorators_module

    # Check for expected functions
    assert hasattr(decorators_module, 'login_required')


@pytest.mark.unit
def test_login_required_with_user_in_session():
    """Test login_required decorator when user is in session"""

    mock_session = {'user_id': '123'}
    mock_redirect = Mock()
    mock_url_for = Mock(return_value='/login')

    with patch('utils.decorators.session', mock_session):
        with patch('utils.decorators.redirect', mock_redirect):
            with patch('utils.decorators.url_for', mock_url_for):

                @login_required
                def test_func():
                    return "success"

                result = test_func()
                assert result == "success"
                mock_redirect.assert_not_called()


@pytest.mark.unit
def test_login_required_without_user_in_session():
    """Test login_required decorator when user is not in session"""

    mock_session = {}
    mock_redirect = Mock(return_value='redirected')
    mock_url_for = Mock(return_value='/login')

    with patch('utils.decorators.session', mock_session):
        with patch('utils.decorators.redirect', mock_redirect):
            with patch('utils.decorators.url_for', mock_url_for):

                @login_required
                def test_func():
                    return "success"

                result = test_func()
                assert result == 'redirected'
                mock_redirect.assert_called_once_with('/login')
                mock_url_for.assert_called_once_with('auth.login')


@pytest.mark.unit
def test_login_required_wraps_function():
    """Test login_required decorator wraps original function"""

    @login_required
    def test_func():
        return "success"

    assert hasattr(test_func, '__wrapped__')
    assert test_func.__name__ == 'test_func'


@pytest.mark.unit
def test_login_required_preserves_function_metadata():
    """Test login_required decorator preserves function metadata"""

    @login_required
    def test_func():
        """Test function docstring"""
        return "success"

    assert test_func.__name__ == 'test_func'
    assert test_func.__doc__ == 'Test function docstring'


@pytest.mark.unit
def test_login_required_with_args_and_kwargs():
    """Test login_required decorator passes args and kwargs"""

    mock_session = {'user_id': '123'}
    mock_redirect = Mock()
    mock_url_for = Mock(return_value='/login')

    with patch('utils.decorators.session', mock_session):
        with patch('utils.decorators.redirect', mock_redirect):
            with patch('utils.decorators.url_for', mock_url_for):

                @login_required
                def test_func(arg1, arg2, kwarg1=None):
                    return f"{arg1}-{arg2}-{kwarg1}"

                result = test_func('a', 'b', kwarg1='c')
                assert result == "a-b-c"
                mock_redirect.assert_not_called()


@pytest.mark.unit
def test_login_required_decorator_callable():
    """Test login_required decorator returns callable"""

    def test_func():
        return "success"

    decorated = login_required(test_func)
    assert callable(decorated)


@pytest.mark.unit
def test_login_required_decorator_on_class_method():
    """Test login_required decorator on class method"""

    class TestClass:
        @login_required
        def test_method(self):
            return "success"

    obj = TestClass()
    assert hasattr(obj.test_method, '__wrapped__')
