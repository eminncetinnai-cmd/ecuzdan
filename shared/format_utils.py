"""
Format utility functions for money, date, and display formatting.

Ana Fonksiyonlar:
  format_money(value)        → "1.234,56"  (Türk Lirası formatı)
  format_date(value)         → "31/12/2025" (gg/aa/yyyy)
  parse_date_input(value)    → "2025-12-31" (yyyy-mm-dd, form girdisinden)
  today_storage()            → "2026-09-01" (bugün, DB formatı)
  today_display()            → "01/09/2026" (bugün, görüntüleme formatı)
"""

import logging
from datetime import datetime
from decimal import Decimal
from typing import Union

logger = logging.getLogger(__name__)

DATE_DISPLAY_FMT = "%d/%m/%Y"
DATE_STORAGE_FMT = "%Y-%m-%d"
DATE_INPUT_FORMATS = ("%d/%m/%Y", "%d.%m.%Y", "%Y-%m-%d")


def format_money(value: Union[int, float, Decimal, str, None]) -> str:
    """
    Para formatı — Türk Lirası formatında (binlik nokta, ondalık virgül).

    Args:
        value: Para değeri (int, float, Decimal veya sayısal string)

    Returns:
        Formatlanmış para string'i (örn: "1.234,56")

    Examples:
        >>> format_money(1234.56)
        '1.234,56'
        >>> format_money(0)
        '0,00'
    """
    try:
        numeric = float(value or 0)
        return "{:,.2f}".format(numeric).replace(",", "X").replace(".", ",").replace("X", ".")
    except (TypeError, ValueError) as e:
        logger.error(f"Para formatlama hatası: {e} (girdi: {value!r})")
        return "0,00"


def format_date(value: Union[str, datetime, None]) -> str:
    """
    Veritabanı (yyyy-mm-dd) → görüntüleme (gg/aa/yyyy) formatına çevirir.

    Args:
        value: Tarih değeri (string veya datetime nesnesi)

    Returns:
        Formatlanmış tarih string'i (örn: "31/12/2025") veya boş string

    Examples:
        >>> format_date("2025-12-31")
        '31/12/2025'
        >>> format_date(None)
        ''
    """
    if not value:
        return ""
    try:
        return datetime.strptime(str(value)[:10], DATE_STORAGE_FMT).strftime(DATE_DISPLAY_FMT)
    except ValueError:
        return str(value)


def _validate_date_parts(dt: datetime) -> None:
    """
    Tarih parçalarını doğrular (1990-2100 aralığı).

    Args:
        dt: datetime nesnesi

    Raises:
        ValueError: Tarih 1990 ile 2100 yılları arasında değilse
    """
    if dt.year < 1990 or dt.year > 2100:
        raise ValueError("Tarih 1990 ile 2100 yılları arasında olmalıdır.")


def parse_date_input(value: Union[str, None]) -> str:
    """
    Form girişi (gg/aa/yyyy veya gg.aa.yyyy) → veritabanı formatı (yyyy-mm-dd).

    Args:
        value: Tarih string'i (gg/aa/yyyy, gg.aa.yyyy veya yyyy-mm-dd)

    Returns:
        Veritabanı formatında tarih string'i (yyyy-mm-dd)

    Raises:
        ValueError: Boş değer, geçersiz format veya 1990-2100 aralığı dışı tarih

    Examples:
        >>> parse_date_input("31/12/2025")
        '2025-12-31'
        >>> parse_date_input("31.12.2025")
        '2025-12-31'
    """
    if not value or not str(value).strip():
        raise ValueError("Tarih girilmelidir.")
    raw = str(value).strip()
    range_error = None
    for fmt in DATE_INPUT_FORMATS:
        try:
            dt = datetime.strptime(raw, fmt)
            _validate_date_parts(dt)
            return dt.strftime(DATE_STORAGE_FMT)
        except ValueError as e:
            if "1990" in str(e) and "2100" in str(e):
                range_error = e
            continue
    if range_error is not None:
        raise range_error
    raise ValueError(
        "Geçerli bir tarih girin (gg/aa/yyyy). Örn. 31/02 veya 32/01/2026 kabul edilmez."
    )


def today_storage() -> str:
    """
    Bugünün tarihini veritabanı formatında (yyyy-mm-dd) döndürür.

    Returns:
        Bugünün tarihi — örn: "2026-09-01"
    """
    return datetime.now().strftime(DATE_STORAGE_FMT)


def today_display() -> str:
    """
    Bugünün tarihini görüntüleme formatında (gg/aa/yyyy) döndürür.

    Returns:
        Bugünün tarihi — örn: "01/09/2026"
    """
    return format_date(today_storage())

