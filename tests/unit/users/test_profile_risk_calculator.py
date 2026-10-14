"""Unit tests for Investor Profile Risk Calculator.

Tests literacy, capacity, tolerance, behavioral, and experience dimension scorers,
risk level classification, confidence calculation, risk boundary rules,
validity expiration dates, and ranking question validation.
"""

from datetime import datetime, timezone
import pytest
from domain.users.services.profile_risk_calculator import (
    DEFAULT_RISK_CLASSES,
    calculate_behavioral_score,
    calculate_capacity_score,
    calculate_confidence,
    calculate_experience_score,
    calculate_final_risk_level,
    calculate_literacy_score,
    calculate_tolerance_score,
    calculate_validity_date,
    classify_risk_level,
    validate_ranking_answer,
)


def test_calculate_literacy_score():
    # Empty answers fallback
    assert calculate_literacy_score([]) == 50
    assert calculate_literacy_score([{"dimension": "capacity", "is_correct": True}]) == 50

    # Calculated correct ratio
    answers = [
        {"dimension": "literacy", "is_correct": True},
        {"dimension": "literacy", "is_correct": False},
        {"dimension": "literacy", "is_correct": True},
        {"dimension": "literacy", "is_correct": None},  # Ignored
    ]
    assert calculate_literacy_score(answers) == pytest.approx(66.666, rel=1e-2)


def test_calculate_capacity_score():
    assert calculate_capacity_score([]) == 50
    answers = [
        {"dimension": "capacity", "score": 8},
        {"dimension": "capacity", "score": 6},
    ]
    # (14 / 20) * 100 = 70.0
    assert calculate_capacity_score(answers) == 70.0


def test_calculate_tolerance_score():
    assert calculate_tolerance_score([]) == 50
    answers = [
        {"dimension": "tolerance", "score": 10},
        {"dimension": "tolerance", "score": 5},
    ]
    # (15 / 20) * 100 = 75.0
    assert calculate_tolerance_score(answers) == 75.0


def test_calculate_behavioral_score():
    assert calculate_behavioral_score([]) == 50
    answers = [
        {"dimension": "behavioral", "score": 4},
        {"dimension": "behavioral", "score": 4},
    ]
    # (8 / 20) * 100 = 40.0
    assert calculate_behavioral_score(answers) == 40.0


def test_calculate_experience_score():
    assert calculate_experience_score([]) == 50
    answers = [
        {"dimension": "experience", "score": 10},
        {"dimension": "experience", "score": 8},
    ]
    # (18 / 20) * 100 = 90.0
    assert calculate_experience_score(answers) == 90.0


def test_classify_risk_level():
    assert classify_risk_level(15) == "Korumacı"
    assert classify_risk_level(25) == "Muhafazakar"
    assert classify_risk_level(40) == "Temkinli"
    assert classify_risk_level(55) == "Dengeli"
    assert classify_risk_level(70) == "Büyüme Odaklı"
    assert classify_risk_level(85) == "Agresif"
    assert classify_risk_level(95) == "Spekülatif"
    # Out of range fallback
    assert classify_risk_level(120) == "Dengeli"


def test_calculate_confidence():
    # Identical scores -> variance = 0, consistency = 100, adequacy = 80 -> avg 90
    conf = calculate_confidence(80, 80, 80, 80, 80)
    assert conf == 90.0

    # High divergence
    conf_div = calculate_confidence(10, 90, 20, 80, 30)
    assert conf_div < 60.0


def test_calculate_final_risk_level_literacy_adjustments():
    # Literacy < 40 -> base_risk *= 0.5
    res = calculate_final_risk_level(
        literacy=30,
        capacity=80,
        tolerance=80,
        behavioral=80,
        experience=80,
    )
    # base_risk was 80, multiplied by 0.5 -> 40
    assert res["base_risk_score"] == 40.0
    assert res["final_risk_level"] == "Temkinli"

    # Literacy between 40 and 60 -> base_risk *= 0.7
    res2 = calculate_final_risk_level(
        literacy=50,
        capacity=80,
        tolerance=80,
        behavioral=80,
        experience=80,
    )
    # base_risk was 80 * 0.7 = 56
    assert res2["base_risk_score"] == 56.0
    assert res2["final_risk_level"] == "Dengeli"


def test_calculate_final_risk_level_capacity_dominance():
    # capacity < tolerance - 20 -> base_risk = capacity
    res = calculate_final_risk_level(
        literacy=90,
        capacity=30,
        tolerance=80,  # 30 < 80 - 20 (60) -> base_risk = 30
        behavioral=80,
        experience=80,
    )
    assert res["base_risk_score"] == 30.0
    assert res["final_risk_level"] == "Muhafazakar"


def test_calculate_final_risk_level_behavioral_and_experience_guards():
    # Behavioral < 40 -> warnings and * 0.8
    # Experience < 30 and base_risk > 60 -> base_risk = 50
    res = calculate_final_risk_level(
        literacy=90,
        capacity=90,
        tolerance=90,
        behavioral=35,
        experience=20,
    )
    # base_risk starts at 90, behavioral < 40 -> 90 * 0.8 = 72, experience < 30 and 72 > 60 -> capped to 50
    assert "Yüksek davranışsal risk tespit edildi" in res["risk_warnings"]
    assert res["base_risk_score"] == 50.0
    assert res["final_risk_level"] == "Dengeli"


def test_calculate_validity_date():
    now = datetime.now(timezone.utc)
    v1 = calculate_validity_date(85)
    assert (v1 - now).days >= 364

    v2 = calculate_validity_date(65)
    assert 178 <= (v2 - now).days <= 181

    v3 = calculate_validity_date(40)
    assert 88 <= (v3 - now).days <= 91


def test_validate_ranking_answer():
    q = {
        "id": "RNK_TEST",
        "options": [{"text": "A"}, {"text": "B"}, {"text": "C"}],
        "correct_order": ["A", "B", "C"],
    }
    # Not a list
    with pytest.raises(ValueError, match="must be a list"):
        validate_ranking_answer(q, "A, B, C")

    # Invalid items
    with pytest.raises(ValueError, match="invalid or duplicate"):
        validate_ranking_answer(q, ["A", "B", "D"])

    # Correct order
    score, is_correct = validate_ranking_answer(q, ["A", "B", "C"])
    assert score == 10
    assert is_correct is True

    # Incorrect order
    score_wrong, is_correct_wrong = validate_ranking_answer(q, ["C", "B", "A"])
    assert score_wrong == 0
    assert is_correct_wrong is False

    # Question without correct_order (neutral)
    q_neutral = {
        "id": "RNK_NEUTRAL",
        "options": [{"text": "A"}, {"text": "B"}],
    }
    score_neu, is_neu = validate_ranking_answer(q_neutral, ["A", "B"])
    assert score_neu == 5
    assert is_neu is None
