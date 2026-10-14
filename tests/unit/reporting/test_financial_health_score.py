"""Unit tests for FinancialHealthScorer (domain/reporting/services/financial_health_score.py).

Tests multi-metric financial health scoring, liquidity ratio, savings rate,
debt-to-income, investment returns, diversification, emergency fund coverage,
recommendation generation, and historical trend analysis.
"""

from datetime import datetime, timedelta
import pytest
from domain.reporting.services.financial_health_score import FinancialHealthScorer
from models import Asset, AssetSector, Transaction, db


def test_get_rating():
    assert FinancialHealthScorer._get_rating(95) == "Mükemmel"
    assert FinancialHealthScorer._get_rating(80) == "Mükemmel"
    assert FinancialHealthScorer._get_rating(70) == "İyi"
    assert FinancialHealthScorer._get_rating(60) == "İyi"
    assert FinancialHealthScorer._get_rating(50) == "Orta"
    assert FinancialHealthScorer._get_rating(40) == "Orta"
    assert FinancialHealthScorer._get_rating(30) == "Zayıf"
    assert FinancialHealthScorer._get_rating(20) == "Zayıf"
    assert FinancialHealthScorer._get_rating(10) == "Kötü"


def test_generate_health_recommendations_all_excellent():
    healthy = {"score": 80}
    recs = FinancialHealthScorer._generate_health_recommendations(
        healthy, healthy, healthy, healthy, healthy, healthy
    )
    assert len(recs) == 1
    assert "Financial health is excellent" in recs[0]


def test_generate_health_recommendations_all_warning():
    weak = {"score": 30}
    recs = FinancialHealthScorer._generate_health_recommendations(
        weak, weak, weak, weak, weak, weak
    )
    assert len(recs) == 6
    assert any("liquidity" in r for r in recs)
    assert any("savings rate" in r for r in recs)
    assert any("debt payments" in r for r in recs)
    assert any("investment portfolio" in r for r in recs)
    assert any("Diversify" in r for r in recs)
    assert any("emergency fund" in r for r in recs)


def test_calculate_financial_health_score_empty_tenant(app):
    with app.app_context():
        res = FinancialHealthScorer.calculate_financial_health_score(tenant_id="empty_tenant_test")
        assert "overall_score" in res
        assert "overall_rating" in res
        assert "components" in res
        # Investment component with no assets returns score 50 (Orta)
        assert res["components"]["investment"]["score"] == 50
        assert res["components"]["investment"]["rating"] == "Orta"


def _create_asset(name, value, liquidity, tenant_id="default"):
    sector = AssetSector.query.first()
    return Asset(
        name=name,
        type="Nakit" if liquidity == "Likit" else "Hisse Senedi",
        value=value,
        purchase_date="2026-01-01",
        purchase_cost=value,
        quantity=1,
        unit_price=value,
        currency="TRY",
        symbol=name[:4].upper(),
        risk_level="Düşük" if liquidity == "Likit" else "Orta",
        liquidity=liquidity,
        sector_id=sector.id,
        tenant_id=tenant_id,
    )


def _create_tx(tx_type, category, amount, date, tenant_id="default"):
    return Transaction(
        type=tx_type,
        category=category,
        status="Ödendi",
        amount=amount,
        date=date,
        tenant_id=tenant_id,
        is_deleted=False,
    )


def test_calculate_financial_health_score_populated_tenant(app, monkeypatch):

    from domain.portfolio.services.performance_calculation import PerformanceCalculator
    from domain.portfolio.services.advanced_allocation import AdvancedAllocationAnalyzer

    monkeypatch.setattr(
        PerformanceCalculator,
        "get_portfolio_performance",
        lambda tenant_id: {"portfolio_twr": 25.0},
    )
    monkeypatch.setattr(
        AdvancedAllocationAnalyzer,
        "get_allocation_by_type",
        lambda tenant_id: {"diversification_score": 85.0, "by_type": {"Hisse": 50, "Altın": 50}},
    )

    with app.app_context():
        tenant_id = "default"
        now = datetime.now()
        recent_date = (now - timedelta(days=15)).strftime("%Y-%m-%d")

        # 1. Assets using valid helper
        db.session.add(_create_asset("Nakit Cüzdan", 60000.0, "Likit", tenant_id))
        db.session.add(_create_asset("Hisse Portföy", 40000.0, "Orta", tenant_id))

        # 2. Transactions using valid helper
        db.session.add(_create_tx("Gelir", "Maaş", 30000.0, recent_date, tenant_id))
        db.session.add(_create_tx("Gider", "Aylık Sabit Gider", 10000.0, recent_date, tenant_id))
        db.session.add(_create_tx("Gider", "Borç", 2000.0, recent_date, tenant_id))
        db.session.commit()

        res = FinancialHealthScorer.calculate_financial_health_score(tenant_id=tenant_id)
        assert res["overall_score"] >= 70.0
        assert res["overall_rating"] in ("Mükemmel", "İyi")
        assert res["components"]["liquidity"]["score"] == 100
        assert res["components"]["investment"]["score"] == 100
        assert res["components"]["diversification"]["score"] == 85.0


def test_scoring_brackets_isolated(app, monkeypatch):
    from domain.portfolio.services.performance_calculation import PerformanceCalculator

    with app.app_context():
        tenant_id = "default"
        now = datetime.now()
        recent_date = (now - timedelta(days=20)).strftime("%Y-%m-%d")

        # Set up moderate ratio asset and expenses
        db.session.add(_create_asset("Nakit Yedek", 3500.0, "Likit", tenant_id))
        db.session.add(_create_tx("Gelir", "Maaş", 10000.0, recent_date, tenant_id))
        # 3000 total expense over 3 months -> 1000/mo -> 3500/1000 = 3.5 months -> score 80
        db.session.add(_create_tx("Gider", "Aylık Sabit Gider", 3000.0, recent_date, tenant_id))
        db.session.add(_create_tx("Gider", "Borç", 2500.0, recent_date, tenant_id))
        db.session.commit()



        # Test investment return brackets
        for ret, expected_score in [
            (25.0, 100),
            (12.0, 80),
            (7.0, 60),
            (2.0, 40),
            (-5.0, 20),
        ]:
            monkeypatch.setattr(
                PerformanceCalculator,
                "get_portfolio_performance",
                lambda tid, r=ret: {"portfolio_twr": r},
            )
            score_data = FinancialHealthScorer._calculate_investment_score(tenant_id)
            assert score_data["score"] == expected_score


def test_get_health_score_trend(app, monkeypatch):
    from domain.portfolio.services.performance_calculation import PerformanceCalculator
    from domain.portfolio.services.advanced_allocation import AdvancedAllocationAnalyzer

    monkeypatch.setattr(
        PerformanceCalculator,
        "get_portfolio_performance",
        lambda tenant_id: {"portfolio_twr": 15.0},
    )
    monkeypatch.setattr(
        AdvancedAllocationAnalyzer,
        "get_allocation_by_type",
        lambda tenant_id: {"diversification_score": 75.0, "by_type": {}},
    )

    with app.app_context():
        trend_res = FinancialHealthScorer.get_health_score_trend(tenant_id="default", months=6)
        assert "current_score" in trend_res
        assert len(trend_res["trend"]) == 6
        assert trend_res["trend_direction"] in ("improving", "declining")


