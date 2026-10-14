"""
Unit Tests - AJAX Helpers
AJAX request handling utility functions
"""


import pytest
from flask import Flask


@pytest.mark.unit
def test_is_ajax_request_with_ajax_header():
    """Test is_ajax_request with AJAX header"""
    app = Flask(__name__)

    with app.test_request_context(headers={'X-Requested-With': 'XMLHttpRequest'}):
        from utils.ajax_helpers import is_ajax_request
        assert is_ajax_request() is True


@pytest.mark.unit
def test_is_ajax_request_without_ajax_header():
    """Test is_ajax_request without AJAX header"""
    app = Flask(__name__)

    with app.test_request_context():
        from utils.ajax_helpers import is_ajax_request
        assert is_ajax_request() is False


@pytest.mark.unit
def test_is_ajax_request_with_different_header():
    """Test is_ajax_request with different header value"""
    app = Flask(__name__)

    with app.test_request_context(headers={'X-Requested-With': 'OtherValue'}):
        from utils.ajax_helpers import is_ajax_request
        assert is_ajax_request() is False


@pytest.mark.unit
def test_ajax_response_success():
    """Test ajax_response with success=True"""
    app = Flask(__name__)

    with app.app_context():
        from utils.ajax_helpers import ajax_response

        response = ajax_response(True, 'Operation successful')

        assert response.status_code == 200
        assert response.json == {'success': True, 'message': 'Operation successful'}


@pytest.mark.unit
def test_ajax_response_failure():
    """Test ajax_response with success=False"""
    app = Flask(__name__)

    with app.app_context():
        from utils.ajax_helpers import ajax_response

        response = ajax_response(False, 'Operation failed')

        assert response.status_code == 200
        assert response.json == {'success': False, 'message': 'Operation failed'}


@pytest.mark.unit
def test_ajax_response_with_redirect():
    """Test ajax_response with redirect URL"""
    app = Flask(__name__)

    with app.app_context():
        from utils.ajax_helpers import ajax_response

        response = ajax_response(True, 'Operation successful', redirect_url='/dashboard')

        assert response.status_code == 200
        assert response.json == {
            'success': True,
            'message': 'Operation successful',
            'redirect': '/dashboard'
        }


@pytest.mark.unit
def test_ajax_response_without_redirect():
    """Test ajax_response without redirect URL"""
    app = Flask(__name__)

    with app.app_context():
        from utils.ajax_helpers import ajax_response

        response = ajax_response(True, 'Operation successful')

        assert response.status_code == 200
        assert 'redirect' not in response.json


@pytest.mark.unit
def test_handle_ajax_or_flash_ajax_success():
    """Test handle_ajax_or_flash with AJAX request and success"""
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'test'

    with app.test_request_context(headers={'X-Requested-With': 'XMLHttpRequest'}):
        from utils.ajax_helpers import handle_ajax_or_flash

        response = handle_ajax_or_flash(True, 'Success message', 'Error message')

        assert response is not None
        assert response.json == {'success': True, 'message': 'Success message'}


@pytest.mark.unit
def test_handle_ajax_or_flash_ajax_failure():
    """Test handle_ajax_or_flash with AJAX request and failure"""
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'test'

    with app.test_request_context(headers={'X-Requested-With': 'XMLHttpRequest'}):
        from utils.ajax_helpers import handle_ajax_or_flash

        response = handle_ajax_or_flash(False, 'Success message', 'Error message')

        assert response is not None
        assert response.json == {'success': False, 'message': 'Error message'}


@pytest.mark.unit
def test_handle_ajax_or_flash_ajax_with_redirect():
    """Test handle_ajax_or_flash with AJAX request and redirect"""
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'test'

    with app.test_request_context(headers={'X-Requested-With': 'XMLHttpRequest'}):
        from utils.ajax_helpers import handle_ajax_or_flash

        response = handle_ajax_or_flash(True, 'Success message', redirect_url='/home')

        assert response is not None
        assert response.json == {
            'success': True,
            'message': 'Success message',
            'redirect': '/home'
        }


@pytest.mark.unit
def test_handle_ajax_or_flash_non_ajax_success():
    """Test handle_ajax_or_flash with non-AJAX request and success"""
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'test'

    with app.test_request_context():
        from flask import get_flashed_messages

        from utils.ajax_helpers import handle_ajax_or_flash

        response = handle_ajax_or_flash(True, 'Success message', 'Error message')

        assert response is None
        messages = get_flashed_messages(with_categories=True)
        assert len(messages) == 1
        assert messages[0] == ('success', 'Success message')


@pytest.mark.unit
def test_handle_ajax_or_flash_non_ajax_failure():
    """Test handle_ajax_or_flash with non-AJAX request and failure"""
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'test'

    with app.test_request_context():
        from flask import get_flashed_messages

        from utils.ajax_helpers import handle_ajax_or_flash

        response = handle_ajax_or_flash(False, 'Success message', 'Error message')

        assert response is None
        messages = get_flashed_messages(with_categories=True)
        assert len(messages) == 1
        assert messages[0] == ('error', 'Error message')


@pytest.mark.unit
def test_handle_ajax_or_flash_non_ajax_no_error_message():
    """Test handle_ajax_or_flash with non-AJAX request and no error message"""
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'test'

    with app.test_request_context():
        from flask import get_flashed_messages

        from utils.ajax_helpers import handle_ajax_or_flash

        response = handle_ajax_or_flash(False, 'Success message')

        assert response is None
        messages = get_flashed_messages(with_categories=True)
        assert len(messages) == 0


@pytest.mark.unit
def test_ajax_error_handler_no_exception():
    """Test ajax_error_handler decorator with no exception"""
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'test'

    with app.test_request_context(headers={'X-Requested-With': 'XMLHttpRequest'}):
        from utils.ajax_helpers import ajax_error_handler

        @ajax_error_handler()
        def test_func():
            return {'result': 'success'}

        result = test_func()
        assert result == {'result': 'success'}


@pytest.mark.unit
def test_ajax_error_handler_with_exception_ajax():
    """Test ajax_error_handler decorator with exception in AJAX request"""
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'test'

    with app.test_request_context(headers={'X-Requested-With': 'XMLHttpRequest'}):
        from utils.ajax_helpers import ajax_error_handler

        @ajax_error_handler(ValueError, 'Validation error: ')
        def test_func():
            raise ValueError('Invalid input')

        result = test_func()
        assert result.json == {'success': False, 'message': 'Validation error: Invalid input'}


@pytest.mark.unit
def test_ajax_error_handler_with_wrong_exception_type():
    """Test ajax_error_handler decorator with wrong exception type"""
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'test'

    with app.test_request_context(headers={'X-Requested-With': 'XMLHttpRequest'}):
        from utils.ajax_helpers import ajax_error_handler

        @ajax_error_handler(ValueError, 'Validation error: ')
        def test_func():
            raise KeyError('Missing key')

        result = test_func()
        # KeyError is now handled as a validation error with specific message
        assert result.json == {'success': False, 'message': "Validation error: 'Missing key'"}


@pytest.mark.unit
def test_ajax_error_handler_no_exception_type():
    """Test ajax_error_handler decorator with no exception type specified"""
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'test'

    with app.test_request_context(headers={'X-Requested-With': 'XMLHttpRequest'}):
        from utils.ajax_helpers import ajax_error_handler

        @ajax_error_handler(error_message_prefix='Error: ')
        def test_func():
            raise ValueError('Test error')

        result = test_func()
        # ValueError is now handled as a validation error with the prefix
        assert result.json == {'success': False, 'message': 'Error: Test error'}


@pytest.mark.unit
def test_ajax_error_handler_non_ajax_request():
    """Test ajax_error_handler decorator with non-AJAX request"""
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'test'

    with app.test_request_context():
        from utils.ajax_helpers import ajax_error_handler

        @ajax_error_handler(ValueError, 'Validation error: ')
        def test_func():
            raise ValueError('Invalid input')

        with pytest.raises(ValueError, match='Invalid input'):
            test_func()


@pytest.mark.unit
def test_handle_crud_operation_success():
    """Test handle_crud_operation with successful operation"""
    from utils.ajax_helpers import handle_crud_operation

    def operation_func():
        return True

    success, message = handle_crud_operation(operation_func, 'Success message', 'Error: ')

    assert success is True
    assert message == 'Success message'


@pytest.mark.unit
def test_handle_crud_operation_false_result():
    """Test handle_crud_operation with false result"""
    from utils.ajax_helpers import handle_crud_operation

    def operation_func():
        return False

    success, message = handle_crud_operation(operation_func, 'Success message', 'Error: ')

    assert success is False
    assert message == 'Error: Kayıt bulunamadı.'


@pytest.mark.unit
def test_handle_crud_operation_exception():
    """Test handle_crud_operation with exception"""
    from utils.ajax_helpers import handle_crud_operation

    def operation_func():
        raise ValueError('Test error')

    success, message = handle_crud_operation(operation_func, 'Success message', 'Error: ')

    assert success is False
    assert message == 'Error: Test error'


@pytest.mark.unit
def test_handle_crud_operation_with_prefix():
    """Test handle_crud_operation with custom error prefix"""
    from utils.ajax_helpers import handle_crud_operation

    def operation_func():
        raise ValueError('Test error')

    success, message = handle_crud_operation(operation_func, 'Success message', 'Custom prefix: ')

    assert success is False
    assert message == 'Custom prefix: Test error'


@pytest.mark.unit
def test_ajax_helpers_logging():
    """Test that logging is configured"""
    from utils.ajax_helpers import logger

    assert logger is not None
    assert logger.name == 'utils.ajax_helpers'


@pytest.mark.unit
def test_ajax_helpers_imports():
    """Test that all required functions are importable"""
    from utils.ajax_helpers import (
        ajax_error_handler,
        ajax_response,
        handle_ajax_or_flash,
        handle_crud_operation,
        is_ajax_request,
    )

    assert callable(is_ajax_request)
    assert callable(ajax_response)
    assert callable(handle_ajax_or_flash)
    assert callable(ajax_error_handler)
    assert callable(handle_crud_operation)
