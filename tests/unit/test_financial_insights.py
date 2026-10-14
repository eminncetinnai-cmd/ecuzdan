"""
Unit Tests - Financial Insights
Financial insights utility functions
"""

import json
from datetime import date
from unittest.mock import mock_open, patch

import pytest

from utils.financial_insights import (
    INSIGHTS_FILE,
    _load_insights,
    get_categories,
    get_daily_insight,
    get_insight_by_date,
    get_insight_count,
)


@pytest.fixture(autouse=True)
def clear_insights_cache():
    """Clear the global cache before each test to ensure isolation"""
    from utils import financial_insights
    financial_insights._insights_cache = None
    financial_insights._cache_date = None
    yield


@pytest.mark.unit
def test_load_insights_file_not_found():
    """Test _load_insights when file doesn't exist"""
    with patch('builtins.open', side_effect=FileNotFoundError):
        result = _load_insights()
        assert result == {"insights": []}


@pytest.mark.unit
def test_load_insights_json_decode_error():
    """Test _load_insights when JSON is invalid"""
    with patch('builtins.open', mock_open(read_data='invalid json')):
        with patch('json.load', side_effect=json.JSONDecodeError('test', 'doc', 1)):
            result = _load_insights()
            assert result == {"insights": []}


@pytest.mark.unit
def test_load_insights_success():
    """Test _load_insights with valid JSON"""
    test_data = {"insights": [{"id": 1, "text": "Test insight"}]}

    with patch('builtins.open', mock_open(read_data=json.dumps(test_data))):
        result = _load_insights()
        assert result == test_data


@pytest.mark.unit
def test_load_insights_caching():
    """Test _load_insights uses cache on same day"""

    test_data = {"insights": [{"id": 1, "text": "Test insight"}]}

    with patch('builtins.open', mock_open(read_data=json.dumps(test_data))):
        # First call loads from file
        result1 = _load_insights()
        assert result1 == test_data

        # Second call should use cache (file not opened)
        result2 = _load_insights()
        assert result2 == test_data


@pytest.mark.unit
def test_get_daily_insight_no_insights():
    """Test get_daily_insight when no insights available"""
    with patch('utils.financial_insights._load_insights', return_value={"insights": []}):
        result = get_daily_insight()
        assert result is None


@pytest.mark.unit
def test_get_daily_insight_success():
    """Test get_daily_insight returns deterministic insight"""
    test_data = {
        "insights": [
            {"id": 1, "text": "Insight 1"},
            {"id": 2, "text": "Insight 2"},
            {"id": 3, "text": "Insight 3"},
        ]
    }

    with patch('utils.financial_insights._load_insights', return_value=test_data):
        result = get_daily_insight()
        assert result is not None
        assert result in test_data["insights"]


@pytest.mark.unit
def test_get_daily_insight_deterministic():
    """Test get_daily_insight returns same insight for same date"""
    test_data = {
        "insights": [
            {"id": 1, "text": "Insight 1"},
            {"id": 2, "text": "Insight 2"},
        ]
    }

    with patch('utils.financial_insights._load_insights', return_value=test_data):
        result1 = get_daily_insight()
        result2 = get_daily_insight()
        assert result1 == result2


@pytest.mark.unit
def test_get_insight_by_date():
    """Test get_insight_by_date for specific date"""
    test_data = {
        "insights": [
            {"id": 1, "text": "Insight 1"},
            {"id": 2, "text": "Insight 2"},
            {"id": 3, "text": "Insight 3"},
        ]
    }

    with patch('utils.financial_insights._load_insights', return_value=test_data):
        test_date = date(2025, 1, 1)
        result = get_insight_by_date(test_date)
        assert result is not None
        assert result in test_data["insights"]


@pytest.mark.unit
def test_get_insight_by_date_no_insights():
    """Test get_insight_by_date when no insights available"""
    with patch('utils.financial_insights._load_insights', return_value={"insights": []}):
        result = get_insight_by_date(date(2025, 1, 1))
        assert result is None


@pytest.mark.unit
def test_get_insight_by_date_deterministic():
    """Test get_insight_by_date returns same insight for same date"""
    test_data = {
        "insights": [
            {"id": 1, "text": "Insight 1"},
            {"id": 2, "text": "Insight 2"},
        ]
    }

    with patch('utils.financial_insights._load_insights', return_value=test_data):
        test_date = date(2025, 1, 1)
        result1 = get_insight_by_date(test_date)
        result2 = get_insight_by_date(test_date)
        assert result1 == result2


@pytest.mark.unit
def test_get_insight_by_date_different_dates():
    """Test get_insight_by_date can return different insights for different dates"""
    test_data = {
        "insights": [
            {"id": 1, "text": "Insight 1"},
            {"id": 2, "text": "Insight 2"},
            {"id": 3, "text": "Insight 3"},
        ]
    }

    with patch('utils.financial_insights._load_insights', return_value=test_data):
        result1 = get_insight_by_date(date(2025, 1, 1))
        result2 = get_insight_by_date(date(2025, 1, 2))
        # Results may or may not be different depending on date calculation
        assert result1 in test_data["insights"]
        assert result2 in test_data["insights"]


@pytest.mark.unit
def test_get_insight_count():
    """Test get_insight_count returns correct count"""
    test_data = {
        "insights": [
            {"id": 1, "text": "Insight 1"},
            {"id": 2, "text": "Insight 2"},
            {"id": 3, "text": "Insight 3"},
        ]
    }

    with patch('utils.financial_insights._load_insights', return_value=test_data):
        count = get_insight_count()
        assert count == 3


@pytest.mark.unit
def test_get_insight_count_empty():
    """Test get_insight_count with no insights"""
    with patch('utils.financial_insights._load_insights', return_value={"insights": []}):
        count = get_insight_count()
        assert count == 0


@pytest.mark.unit
def test_get_insight_count_missing_insights_key():
    """Test get_insight_count when insights key is missing"""
    with patch('utils.financial_insights._load_insights', return_value={}):
        count = get_insight_count()
        assert count == 0


@pytest.mark.unit
def test_get_categories():
    """Test get_categories returns categories list"""
    test_data = {
        "categories": ["Budgeting", "Investing", "Saving"]
    }

    with patch('utils.financial_insights._load_insights', return_value=test_data):
        categories = get_categories()
        assert categories == ["Budgeting", "Investing", "Saving"]


@pytest.mark.unit
def test_get_categories_empty():
    """Test get_categories when no categories"""
    with patch('utils.financial_insights._load_insights', return_value={"categories": []}):
        categories = get_categories()
        assert categories == []


@pytest.mark.unit
def test_get_categories_missing_key():
    """Test get_categories when categories key is missing"""
    with patch('utils.financial_insights._load_insights', return_value={}):
        categories = get_categories()
        assert categories == []


@pytest.mark.unit
def test_insights_file_path():
    """Test INSIGHTS_FILE path is set correctly"""
    assert INSIGHTS_FILE is not None
    assert 'financial_insights.json' in INSIGHTS_FILE


@pytest.mark.unit
def test_insight_structure():
    """Test that returned insights have expected structure"""
    test_data = {
        "insights": [
            {"id": 1, "category": "Budgeting", "text": "Test insight", "source": "Test"}
        ]
    }

    with patch('utils.financial_insights._load_insights', return_value=test_data):
        result = get_daily_insight()
        assert result is not None
        assert "id" in result
        assert "text" in result


@pytest.mark.unit
def test_date_calculation():
    """Test date number calculation for insight selection"""
    test_data = {
        "insights": [
            {"id": 1, "text": "Insight 1"},
            {"id": 2, "text": "Insight 2"},
        ]
    }

    with patch('utils.financial_insights._load_insights', return_value=test_data):
        test_date = date(2025, 1, 1)
        # Date number should be 20250101
        # Index should be 20250101 % 2 = 1
        result = get_insight_by_date(test_date)
        assert result["id"] == 2
