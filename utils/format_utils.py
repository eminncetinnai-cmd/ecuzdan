"""
Format utility functions for money, date, and display formatting.
"""

import logging
from datetime import datetime

logger = logging.getLogger(__name__)

DATE_DISPLAY_FMT = "%d/%m/%Y"
DATE_STORAGE_FMT = "%Y-%m-%d"
DATE_INPUT_FORMATS = ("%d/%m/%Y", "%d.%m.%Y", "%Y-%m-%d")


def format_money(value):
    """
    Para formatı - Türk Lirası formatında

    Args:
        value: Para değeri (int, float veya sayısal string)

    Returns:
        Formatlanmış para string'i (örn: "1.234,56")
    """
    try:
        # String olarak gelen sayısal değerleri float'a çevir
        numeric = float(value or 0)
        return "{:,.2f}".format(numeric).replace(",", "X").replace(".", ",").replace("X", ".")
    except (TypeError, ValueError) as e:
        logger.error(f"Para formatlama hatası: {e} (girdi: {value!r})")
        return "0,00"


def format_date(value):
    """
    Veritabanı (yyyy-mm-dd) → gg/aa/yyyy

    Args:
        value: Tarih değeri (string veya datetime)

    Returns:
        Formatlanmış tarih string'i (örn: "31/12/2025")
    """
    if not value:
        return ""
    try:
        return datetime.strptime(str(value)[:10], DATE_STORAGE_FMT).strftime(DATE_DISPLAY_FMT)
    except ValueError:
        return str(value)


def _validate_date_parts(dt):
    """
    Tarih parçalarını doğrular

    Args:
        dt: datetime nesnesi

    Raises:
        ValueError: Tarih 1990 ile 2100 yılları arasında değilse
    """
    if dt.year < 1990 or dt.year > 2100:
        raise ValueError("Tarih 1990 ile 2100 yılları arasında olmalıdır.")


def parse_date_input(value):
    """
    Form girişi (gg/aa/yyyy) → veritabanı yyyy-mm-dd; geçersiz tarih reddedilir.

    Args:
        value: Tarih string'i

    Returns:
        Veritabanı formatında tarih string'i (yyyy-mm-dd)

    Raises:
        ValueError: Geçersiz tarih
    """
    if not value or not str(value).strip():
        raise ValueError("Tarih girilmelidir.")
    raw = str(value).strip()
    last_error = None
    for fmt in DATE_INPUT_FORMATS:
        try:
            dt = datetime.strptime(raw, fmt)
            _validate_date_parts(dt)
            return dt.strftime(DATE_STORAGE_FMT)
        except ValueError as e:
            last_error = e
            continue
    if isinstance(last_error, ValueError) and "1990" in str(last_error):
        raise last_error
    raise ValueError(
        "Geçerli bir tarih girin (gg/aa/yyyy). Örn. 31/02 veya 32/01/2026 kabul edilmez."
    )


def today_storage():
    """
    Bugünün tarihini veritabanı formatında döndürür

    Returns:
        Bugünün tarihi (yyyy-mm-dd formatında)
    """
    return datetime.now().strftime(DATE_STORAGE_FMT)


def today_display():
    """
    Bugünün tarihini görüntüleme formatında döndürür

    Returns:
        Bugünün tarihi (gg/aa/yyyy formatında)
    """
    return format_date(today_storage())
