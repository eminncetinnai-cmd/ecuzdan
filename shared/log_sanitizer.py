"""
shared/log_sanitizer.py — Hassas veri log maskesi

Log mesajlarına hassas alanlar sızmasın diye kullanılan yardımcılar.
Domain/Application katmanlarında import edilebilir, Flask gerektirmez.

Kullanım:
    from shared.log_sanitizer import mask_email, mask_bearer, redact_dict

    logger.info(f"Login attempt: {mask_email(email)}")
    logger.debug(f"Headers: {redact_dict(dict(request.headers))}")
"""

import re
from typing import Any

# Maskelenecek alan adları (küçük harf, kısmi eşleşme yeterli)
_SENSITIVE_KEYS = frozenset({
    'password', 'passwd', 'secret', 'token', 'access_token', 'refresh_token',
    'id_token', 'api_key', 'apikey', 'authorization', 'auth', 'client_secret',
    'private_key', 'csrf_token', 'state', 'code', 'nonce', 'otp', 'pin',
    'credit_card', 'card_number', 'cvv', 'ssn', 'iban', 'bank_account',
})

_REDACTED = '[REDACTED]'


def mask_email(email: str | None) -> str:
    """E-posta adresini kısmen maskeler: john@example.com → j***@example.com"""
    if not email or '@' not in email:
        return _REDACTED
    local, domain = email.split('@', 1)
    if len(local) <= 1:
        return f"{local}***@{domain}"
    return f"{local[0]}***@{domain}"


def mask_provider_id(provider_id: str | None) -> str:
    """OAuth sağlayıcı ID'sini maskeler: 1234567890 → 123...890"""
    if not provider_id:
        return _REDACTED
    s = str(provider_id)
    if len(s) <= 6:
        return '***'
    return f"{s[:3]}...{s[-3:]}"


def mask_bearer(token: str | None) -> str:
    """Bearer token'ı maskeler: eyJhb... → eyJ***"""
    if not token:
        return _REDACTED
    if len(token) <= 8:
        return '***'
    return f"{token[:4]}***"


def redact_dict(data: dict[str, Any], *, max_value_len: int = 200) -> dict[str, str]:
    """
    Sözlükteki hassas anahtarları maskeler.

    Güvenli olmayan dict'leri (request.headers, form verileri) log'a
    yazmadan önce bu fonksiyondan geçirin.

    Args:
        data: Maskelenecek sözlük.
        max_value_len: Değerlerin maksimum uzunluğu (kesilir). DoS koruması.

    Returns:
        Maskelenmiş string değerli yeni bir dict.

    Örnek:
        logger.debug(f"Form: {redact_dict(dict(request.form))}")
    """
    result: dict[str, str] = {}
    for key, value in data.items():
        key_lower = str(key).lower()
        is_sensitive = any(s in key_lower for s in _SENSITIVE_KEYS)
        if is_sensitive:
            result[key] = _REDACTED
        else:
            str_val = str(value)
            if len(str_val) > max_value_len:
                str_val = str_val[:max_value_len] + '...[truncated]'
            result[key] = str_val
    return result


def redact_url_params(url: str) -> str:
    """
    URL'deki hassas query parametrelerini maskeler.

    Örnek:
        /callback?code=abc123&state=xyz → /callback?code=[REDACTED]&state=[REDACTED]
    """
    def _replace_param(match: re.Match) -> str:
        key = match.group(1)
        if any(s in key.lower() for s in _SENSITIVE_KEYS):
            return f"{key}={_REDACTED}"
        return match.group(0)

    return re.sub(r'([^?&=]+)=([^&]*)', _replace_param, url)
