"""
AJAX Response Helpers
AJAX request handling için yardımcı fonksiyonlar
Duplicate kodu azaltmak için ortak AJAX response pattern'leri
"""

import logging
from functools import wraps

from flask import flash, jsonify, request

logger = logging.getLogger(__name__)


def is_ajax_request():
    """Request'in AJAX olup olmadığını kontrol eder"""
    return request.headers.get('X-Requested-With') == 'XMLHttpRequest'


def ajax_response(success, message, redirect_url=None):
    """
    Standart AJAX response döner

    Args:
        success: İşlem başarılı mı
        message: Mesaj
        redirect_url: Opsiyonel yönlendirme URL'si

    Returns:
        JSON response
    """
    response = {'success': success, 'message': message}
    if redirect_url:
        response['redirect'] = redirect_url
    return jsonify(response)


def handle_ajax_or_flash(success, success_message, error_message=None, redirect_url=None):
    """
    AJAX veya normal request için uygun response döner

    Args:
        success: İşlem başarılı mı
        success_message: Başarı mesajı
        error_message: Hata mesajı (opsiyonel)
        redirect_url: Yönlendirme URL'si (opsiyonel)

    Returns:
        AJAX ise JSON response, değilse None (flash mesajı ile)
    """
    if is_ajax_request():
        return ajax_response(success, success_message if success else error_message, redirect_url)
    else:
        if success:
            flash(success_message, 'success')
        elif error_message:
            flash(error_message, 'error')
        return None


def ajax_error_handler(exception_type=None, error_message_prefix=''):
    """
    AJAX hata handling için decorator

    Args:
        exception_type: Yakalanacak exception tipi (None ise tüm exception'lar)
        error_message_prefix: Hata mesajı öneki

    Returns:
        Decorator function
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except (ValueError, KeyError, TypeError) as e:
                if is_ajax_request():
                    if exception_type and isinstance(e, exception_type):
                        return ajax_response(False, f'{error_message_prefix}{str(e)}')
                    else:
                        logger.error(f"Validation error in {func.__name__}: {e}")
                        return ajax_response(False, f'{error_message_prefix}{str(e)}')
                else:
                    raise
            except Exception as e:
                if is_ajax_request():
                    logger.error(f"Unexpected error in {func.__name__}: {e}", exc_info=True)
                    return ajax_response(False, 'Beklenmeyen bir hata oluştu.')
                else:
                    raise
        return wrapper
    return decorator


def handle_crud_operation(operation_func, success_message, error_message_prefix=''):
    """
    CRUD işlemleri için ortak error handling

    Args:
        operation_func: Çalıştırılacak fonksiyon
        success_message: Başarı mesajı
        error_message_prefix: Hata mesajı öneki

    Returns:
        (success, message) tuple
    """
    try:
        result = operation_func()
        if result:
            return True, success_message
        else:
            return False, f'{error_message_prefix}Kayıt bulunamadı.'
    except (ValueError, KeyError, TypeError) as e:
        logger.error(f"CRUD validation error: {e}")
        return False, f'{error_message_prefix}{str(e)}'
    except Exception as e:
        logger.error(f"CRUD operation error: {e}", exc_info=True)
        return False, f'{error_message_prefix}{str(e)}'
