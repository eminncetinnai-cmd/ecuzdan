from datetime import date
from decimal import Decimal
from types import SimpleNamespace

import pytest

from domain.planning.models import (
    CanonicalPlan,
    PlanFilters,
    PlanFlow,
    PlanLifecycle,
    PlanStatus,
)
from domain.planning.services.occurrence_service import OccurrenceCalculator


def make_plan(**overrides):
    values = {
        'id': 1,
        'tenant_id': 'default',
        'name': 'Maaş Emin',
        'category': 'Maaş / Ücret Geliri',
        'flow_type': 'Gelir',
        'amount': Decimal('78000'),
        'plan_type': 'Dönemsel',
        'frequency': 'Aylık',
        'installments': 4,
        'payment_day': 10,
        'start_date': '2026-08-19',
        'end_date': None,
        'status': 'Aktif',
        'note': None,
        'target_asset_id': None,
    }
    values.update(overrides)
    return SimpleNamespace(**values)


def test_legacy_plan_maps_to_canonical_lifecycle_and_occurrence_limit():
    plan = CanonicalPlan.from_model(make_plan())

    assert plan.flow is PlanFlow.INCOME
    assert plan.lifecycle is PlanLifecycle.INSTALLMENT
    assert plan.start_date == date(2026, 8, 19)
    assert plan.occurrence_limit == 4
    assert plan.status is PlanStatus.ACTIVE


def test_start_date_is_anchor_and_payment_day_does_not_backfill():
    plan = CanonicalPlan.from_model(make_plan())

    occurrences = OccurrenceCalculator.generate(plan)

    assert [item.scheduled_date.isoformat() for item in occurrences] == [
        '2026-09-10',
        '2026-10-10',
        '2026-11-10',
        '2026-12-10',
    ]


def test_month_end_payment_day_is_clamped_without_overflow():
    plan = CanonicalPlan.from_model(
        make_plan(
            id=2,
            name='Kira',
            plan_type='Dönemsel',
            installments=3,
            payment_day=31,
            start_date='2026-08-19',
        )
    )

    occurrences = OccurrenceCalculator.generate(plan)

    assert [item.scheduled_date.isoformat() for item in occurrences] == [
        '2026-08-31',
        '2026-09-30',
        '2026-10-31',
    ]


def test_filters_match_unified_plan_properties():
    plan = CanonicalPlan.from_model(make_plan())

    assert PlanFilters(flow=PlanFlow.INCOME).matches(plan)
    assert PlanFilters(lifecycle=PlanLifecycle.INSTALLMENT).matches(plan)
    assert PlanFilters(search='maaş').matches(plan)
    assert not PlanFilters(investment_only=True).matches(plan)


def test_indefinite_plan_lifecycle_and_none_remaining():
    """Verify indefinite subscription plans map to INDEFINITE with None remaining months/debt"""
    plan = CanonicalPlan.from_model(
        make_plan(
            id=10,
            name='Netflix',
            category='Abonelikler',
            flow_type='Gider',
            amount=Decimal('299.99'),
            plan_type='Abonelik',
            installments=0,
            payment_day=5,
            start_date='2026-10-01',
        )
    )

    assert plan.lifecycle is PlanLifecycle.INDEFINITE
    assert plan.is_indefinite is True
    assert plan.occurrence_limit is None
    assert plan.months_remaining is None
    assert plan.remaining_total_amount is None


def test_indefinite_dca_plan_lifecycle_and_investment_flag():
    """Verify indefinite DCA plans map to INDEFINITE and is_investment is True"""
    plan = CanonicalPlan.from_model(
        make_plan(
            id=11,
            name='Aylık Fon Alımı',
            category='Yatırım',
            flow_type='Yatırım',
            amount=Decimal('5000'),
            plan_type='DCA',
            installments=0,
            payment_day=15,
            start_date='2026-10-01',
            target_asset_id=99,
        )
    )

    assert plan.lifecycle is PlanLifecycle.INDEFINITE
    assert plan.is_investment is True
    assert plan.is_cashflow is False
    assert plan.months_remaining is None
    assert plan.remaining_total_amount is None


def test_installment_plan_calculated_remaining_and_debt():
    """Verify installment plans calculate months_remaining and total remaining debt accurately"""
    plan = CanonicalPlan.from_model(
        make_plan(
            id=12,
            name='Telefon Taksiti',
            category='Elektronik',
            flow_type='Gider',
            amount=Decimal('2500'),
            plan_type='Taksit',
            installments=6,
            payment_day=20,
            start_date=date.today().isoformat(),
        )
    )

    assert plan.lifecycle is PlanLifecycle.INSTALLMENT
    assert plan.is_indefinite is False
    assert plan.occurrence_limit == 6
    assert plan.months_remaining == 6
    assert plan.remaining_total_amount == Decimal('15000')


def test_indefinite_occurrence_calculator_rolling_generation():
    """Verify OccurrenceCalculator generates rolling 3-month future occurrences for indefinite plans"""
    plan = CanonicalPlan.from_model(
        make_plan(
            id=13,
            name='Ev İnterneti',
            category='Faturalar',
            flow_type='Gider',
            amount=Decimal('450'),
            plan_type='Abonelik',
            installments=0,
            payment_day=15,
            start_date='2026-10-01',
        )
    )

    occurrences = OccurrenceCalculator.generate(plan, today=date(2026, 10, 12))
    assert len(occurrences) >= 3
    # Occurrences advance monthly on the 15th
    assert occurrences[0].scheduled_date == date(2026, 10, 15)
    assert occurrences[1].scheduled_date == date(2026, 11, 15)
    assert occurrences[2].scheduled_date == date(2026, 12, 15)


def test_inactive_plan_months_remaining_is_zero():
    """Verify completed or cancelled plans return 0 remaining months and 0 total debt"""
    completed_plan = CanonicalPlan.from_model(
        make_plan(
            id=14,
            installments=12,
            status='Tamamlandı',
        )
    )
    assert completed_plan.months_remaining == 0
    assert completed_plan.remaining_total_amount == Decimal('0')

    cancelled_plan = CanonicalPlan.from_model(
        make_plan(
            id=15,
            installments=12,
            status='İptal',
        )
    )
    assert cancelled_plan.months_remaining == 0
    assert cancelled_plan.remaining_total_amount == Decimal('0')


@pytest.mark.unit
def test_plan_is_completed_property_and_countdown_suppression():
    """Verify is_completed returns True when all installments paid or status is COMPLETED, and suppresses countdown."""
    finished_installment = CanonicalPlan.from_model(
        make_plan(
            id=20,
            installments=6,
            payment_day=15,
            paid_count=6,
            status='Aktif',
        )
    )
    assert finished_installment.is_completed is True
    assert finished_installment.months_remaining == 0
    assert finished_installment.remaining_total_amount == Decimal('0')
    assert finished_installment.payment_countdown is None

    explicitly_completed = CanonicalPlan.from_model(
        make_plan(
            id=21,
            installments=12,
            status='Tamamlandı',
        )
    )
    assert explicitly_completed.is_completed is True
    assert explicitly_completed.payment_countdown is None


@pytest.mark.unit
def test_plan_is_completed_false_when_installments_remain():
    """Verify is_completed returns False when installments remain and countdown is computed."""
    active_installment = CanonicalPlan.from_model(
        make_plan(
            id=22,
            amount=Decimal('1000'),
            installments=12,
            payment_day=15,
            paid_count=4,
            status='Aktif',
        )
    )
    assert active_installment.is_completed is False
    assert active_installment.months_remaining == 8
    assert active_installment.remaining_total_amount == Decimal('8000')
    assert active_installment.payment_countdown is not None


@pytest.mark.unit
def test_plan_is_completed_false_for_indefinite_plans():
    """Verify indefinite recurring plans are never marked as completed by count."""
    indefinite_plan = CanonicalPlan.from_model(
        make_plan(
            id=23,
            installments=0,
            plan_type='Abonelik',
            paid_count=50,
            status='Aktif',
        )
    )
    assert indefinite_plan.is_completed is False
    assert indefinite_plan.months_remaining is None
    assert indefinite_plan.payment_countdown is not None


@pytest.mark.unit
def test_plan_progress_pct_and_estimated_end_date():
    """Verify progress_pct returns correct percentage and estimated_end_date_display formats month & year."""
    plan = CanonicalPlan.from_model(
        make_plan(
            id=30,
            amount=Decimal('2000'),
            installments=10,
            paid_count=4,
            status='Aktif',
            end_date='2027-05-15',
        )
    )
    assert plan.progress_pct == 40
    assert plan.estimated_end_date_display == 'Mayıs 2027'

    completed = CanonicalPlan.from_model(
        make_plan(
            id=31,
            amount=Decimal('2000'),
            installments=10,
            paid_count=10,
            status='Aktif',
        )
    )
    assert completed.progress_pct == 100
    assert completed.is_completed is True

