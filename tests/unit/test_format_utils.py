"""
Unit Tests - Format Utils
Format utility functions for money, date, and display formatting tests
"""

from datetime import datetime

import pytest

from utils.format_utils import (
    DATE_DISPLAY_FMT,
    DATE_INPUT_FORMATS,
    DATE_STORAGE_FMT,
    _validate_date_parts,
    format_date,
    format_money,
    parse_date_input,
    today_display,
    today_storage,
)


@pytest.mark.unit
def test_format_utils_module_imports():
    """Test format_utils module can be imported"""
    from utils.format_utils import format_money
    assert format_money is not None


@pytest.mark.unit
def test_format_utils_module_structure():
    """Test format_utils module structure"""
    import utils.format_utils as format_module

    # Check for expected functions
    assert hasattr(format_module, 'format_money')
    assert hasattr(format_module, 'format_date')
    assert hasattr(format_module, '_validate_date_parts')
    assert hasattr(format_module, 'parse_date_input')
    assert hasattr(format_module, 'today_storage')
    assert hasattr(format_module, 'today_display')


@pytest.mark.unit
def test_format_money_integer():
    """Test format_money with integer"""
    result = format_money(1234)
    assert result == "1.234,00"


@pytest.mark.unit
def test_format_money_float():
    """Test format_money with float"""
    result = format_money(1234.56)
    assert result == "1.234,56"


@pytest.mark.unit
def test_format_money_string():
    """Test format_money with string"""
    result = format_money("1234.56")
    assert result == "1.234,56"


@pytest.mark.unit
def test_format_money_zero():
    """Test format_money with zero"""
    result = format_money(0)
    assert result == "0,00"


@pytest.mark.unit
def test_format_money_none():
    """Test format_money with None"""
    result = format_money(None)
    assert result == "0,00"


@pytest.mark.unit
def test_format_money_large_number():
    """Test format_money with large number"""
    result = format_money(1234567890.12)
    assert result == "1.234.567.890,12"


@pytest.mark.unit
def test_format_money_negative():
    """Test format_money with negative number"""
    result = format_money(-1234.56)
    assert result == "-1.234,56"


@pytest.mark.unit
def test_format_money_invalid_string():
    """Test format_money with invalid string"""
    result = format_money("invalid")
    assert result == "0,00"


@pytest.mark.unit
def test_format_date_string():
    """Test format_date with storage format string"""
    result = format_date("2025-12-31")
    assert result == "31/12/2025"


@pytest.mark.unit
def test_format_date_datetime():
    """Test format_date with datetime object"""
    result = format_date(datetime(2025, 12, 31))
    assert result == "31/12/2025"


@pytest.mark.unit
def test_format_date_none():
    """Test format_date with None"""
    result = format_date(None)
    assert result == ""


@pytest.mark.unit
def test_format_date_empty_string():
    """Test format_date with empty string"""
    result = format_date("")
    assert result == ""


@pytest.mark.unit
def test_format_date_invalid_format():
    """Test format_date with invalid format returns original"""
    result = format_date("invalid-date")
    assert result == "invalid-date"


@pytest.mark.unit
def test_format_date_with_time():
    """Test format_date with datetime including time"""
    result = format_date("2025-12-31 15:30:00")
    assert result == "31/12/2025"


@pytest.mark.unit
def test_validate_date_parts_valid():
    """Test _validate_date_parts with valid date"""
    dt = datetime(2025, 12, 31)
    # Should not raise
    _validate_date_parts(dt)


@pytest.mark.unit
def test_validate_date_parts_too_early():
    """Test _validate_date_parts with date before 1990"""
    dt = datetime(1989, 12, 31)
    try:
        _validate_date_parts(dt)
        assert False, "Should raise ValueError"
    except ValueError as e:
        assert "1990" in str(e)


@pytest.mark.unit
def test_validate_date_parts_too_late():
    """Test _validate_date_parts with date after 2100"""
    dt = datetime(2101, 1, 1)
    try:
        _validate_date_parts(dt)
        assert False, "Should raise ValueError"
    except ValueError as e:
        assert "2100" in str(e)


@pytest.mark.unit
def test_validate_date_parts_boundary_1990():
    """Test _validate_date_parts with 1990 boundary"""
    dt = datetime(1990, 1, 1)
    # Should not raise
    _validate_date_parts(dt)


@pytest.mark.unit
def test_validate_date_parts_boundary_2100():
    """Test _validate_date_parts with 2100 boundary"""
    dt = datetime(2100, 12, 31)
    # Should not raise
    _validate_date_parts(dt)


@pytest.mark.unit
def test_parse_date_input_slash_format():
    """Test parse_date_input with slash format"""
    result = parse_date_input("31/12/2025")
    assert result == "2025-12-31"


@pytest.mark.unit
def test_parse_date_input_dot_format():
    """Test parse_date_input with dot format"""
    result = parse_date_input("31.12.2025")
    assert result == "2025-12-31"


@pytest.mark.unit
def test_parse_date_input_dash_format():
    """Test parse_date_input with dash format"""
    result = parse_date_input("2025-12-31")
    assert result == "2025-12-31"


@pytest.mark.unit
def test_parse_date_input_empty():
    """Test parse_date_input with empty string"""
    try:
        parse_date_input("")
        assert False, "Should raise ValueError"
    except ValueError as e:
        assert "girilmelidir" in str(e)


@pytest.mark.unit
def test_parse_date_input_none():
    """Test parse_date_input with None"""
    try:
        parse_date_input(None)
        assert False, "Should raise ValueError"
    except ValueError as e:
        assert "girilmelidir" in str(e)


@pytest.mark.unit
def test_parse_date_input_whitespace():
    """Test parse_date_input with whitespace"""
    try:
        parse_date_input("   ")
        assert False, "Should raise ValueError"
    except ValueError as e:
        assert "girilmelidir" in str(e)


@pytest.mark.unit
def test_parse_date_input_invalid_format():
    """Test parse_date_input with invalid format"""
    try:
        parse_date_input("invalid")
        assert False, "Should raise ValueError"
    except ValueError as e:
        assert "Geçerli bir tarih" in str(e)


@pytest.mark.unit
def test_parse_date_input_invalid_day():
    """Test parse_date_input with invalid day"""
    try:
        parse_date_input("32/01/2026")
        assert False, "Should raise ValueError"
    except ValueError as e:
        assert "Geçerli bir tarih" in str(e)


@pytest.mark.unit
def test_parse_date_input_invalid_month():
    """Test parse_date_input with invalid month"""
    try:
        parse_date_input("31/13/2026")
        assert False, "Should raise ValueError"
    except ValueError as e:
        assert "Geçerli bir tarih" in str(e)


@pytest.mark.unit
def test_parse_date_input_too_early():
    """Test parse_date_input with date before 1990"""
    try:
        parse_date_input("01/01/1989")
        assert False, "Should raise ValueError"
    except ValueError as e:
        assert "1990" in str(e)


@pytest.mark.unit
def test_parse_date_input_too_late():
    """Test parse_date_input with date after 2100"""
    try:
        parse_date_input("01/01/2101")
        assert False, "Should raise ValueError"
    except ValueError as e:
        assert "2100" in str(e)


@pytest.mark.unit
def test_parse_date_input_with_whitespace():
    """Test parse_date_input with surrounding whitespace"""
    result = parse_date_input(" 31/12/2025 ")
    assert result == "2025-12-31"


@pytest.mark.unit
def test_today_storage():
    """Test today_storage returns current date in storage format"""
    result = today_storage()
    # Should match yyyy-mm-dd format
    assert len(result) == 10
    assert result[4] == '-'
    assert result[7] == '-'


@pytest.mark.unit
def test_today_display():
    """Test today_display returns current date in display format"""
    result = today_display()
    # Should match dd/mm/yyyy format
    assert len(result) == 10
    assert result[2] == '/'
    assert result[5] == '/'


@pytest.mark.unit
def test_date_format_constants():
    """Test date format constants are defined"""
    assert DATE_DISPLAY_FMT == "%d/%m/%Y"
    assert DATE_STORAGE_FMT == "%Y-%m-%d"
    assert len(DATE_INPUT_FORMATS) == 3


@pytest.mark.unit
def test_format_utils_module_has_logging():
    """Test format_utils module has logging configured"""
    import utils.format_utils as format_module
    assert hasattr(format_module, 'logger')


@pytest.mark.unit
def test_format_money_negative_zero():
    """Test format_money with negative zero"""
    result = format_money(-0)
    assert result == "0,00"


@pytest.mark.unit
def test_format_money_small_decimal():
    """Test format_money with small decimal"""
    result = format_money(0.01)
    assert result == "0,01"


@pytest.mark.unit
def test_format_money_rounding():
    """Test format_money rounds correctly"""
    result = format_money(1234.567)
    assert result == "1.234,57"
