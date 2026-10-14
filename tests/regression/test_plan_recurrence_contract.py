"""Regression coverage for plan occurrence dates and recurrence counts."""

import pytest

from models import Transaction
from repositories.financial_repository import FinancialRepository
from validators.request_validators import plan_form_from_request


@pytest.mark.regression
def test_monthly_plan_starts_on_or_after_start_date(app):
    """A monthly plan must never generate an occurrence before its start date."""
    with app.app_context():
        repo = FinancialRepository()
        plan = repo.add_recurring_plan(
            name='Maaş Emin',
            category='Maaş',
            amount=50000,
            installments=4,
            payment_day=10,
            start_date='2026-08-19',
            tenant_id='default',
            plan_type='Dönemsel',
            frequency='Aylık',
        )

        dates = [
            tx.date
            for tx in Transaction.query.filter_by(source_id=plan.id, source_type='plan')
            .order_by(Transaction.installment_number)
            .all()
        ]

        assert dates == ['2026-09-10', '2026-10-10', '2026-11-10', '2026-12-10']
        assert all(date >= plan.start_date for date in dates)


@pytest.mark.regression
def test_periodic_plan_uses_installment_count(app):
    """A finite periodic plan creates the requested number of periods."""
    with app.app_context():
        repo = FinancialRepository()
        plan = repo.add_recurring_plan(
            name='Dönemsel Gelir',
            category='Maaş',
            amount=1000,
            installments=4,
            payment_day=25,
            start_date='2026-08-05',
            tenant_id='default',
            plan_type='Dönemsel',
            frequency='Aylık',
        )

        transactions = Transaction.query.filter_by(source_id=plan.id, source_type='plan').all()
        assert len(transactions) == 4
        assert {tx.installment_number for tx in transactions} == {1, 2, 3, 4}


@pytest.mark.regression
@pytest.mark.parametrize(
    ('frequency', 'expected_dates'),
    [
        ('3-Aylık', ['2026-11-10', '2027-02-10', '2027-05-10']),
        ('Yıllık', ['2027-08-10', '2028-08-10', '2029-08-10']),
        ('Haftalık', ['2026-08-19', '2026-08-26', '2026-09-02']),
    ],
)
def test_periodic_frequency_advances_from_first_valid_occurrence(app, frequency, expected_dates):
    """Periodic frequency advances from the first occurrence on/after start_date."""
    with app.app_context():
        repo = FinancialRepository()
        plan = repo.add_recurring_plan(
            name=f'{frequency} planı',
            category='Maaş',
            amount=1000,
            installments=3,
            payment_day=10,
            start_date='2026-08-19',
            tenant_id='default',
            plan_type='Dönemsel',
            frequency=frequency,
        )

        dates = [
            tx.date
            for tx in Transaction.query.filter_by(source_id=plan.id, source_type='plan')
            .order_by(Transaction.installment_number)
            .all()
        ]
        assert dates == expected_dates


@pytest.mark.regression
def test_rolling_plan_never_backfills_before_start_date(app):
    """Abonelik/DCA rolling generation keeps its three-period window in the future."""
    with app.app_context():
        repo = FinancialRepository()
        plan = repo.add_recurring_plan(
            name='Abonelik',
            category='Kredi Kartı',
            amount=250,
            installments=0,
            payment_day=10,
            start_date='2026-08-19',
            tenant_id='default',
            plan_type='Abonelik',
            frequency='Aylık',
        )
        repo.generate_rolling_transactions('default')

        dates = [
            tx.date
            for tx in Transaction.query.filter_by(source_id=plan.id, source_type='plan')
            .order_by(Transaction.date)
            .all()
        ]
        assert '2026-08-10' not in dates
        assert dates[:3] == ['2026-09-10', '2026-10-10', '2026-11-10']
        assert all(date >= plan.start_date for date in dates)


@pytest.mark.regression
def test_payment_before_plan_start_is_rejected(app):
    """Manual payment cannot create a financial event before the plan anchor."""
    with app.app_context():
        repo = FinancialRepository()
        plan = repo.add_recurring_plan(
            name='Tarihli Plan',
            category='Maaş',
            amount=1000,
            installments=2,
            payment_day=10,
            start_date='2026-08-19',
            tenant_id='default',
        )

        with pytest.raises(ValueError, match='başlangıç tarihinden önce'):
            repo.create_payment(
                plan.id,
                1000,
                '2026-08-18',
                1,
                tenant_id='default',
            )


@pytest.mark.regression
def test_plan_form_rejects_invalid_date_range():
    """Request validation rejects an end date before the start date."""
    with pytest.raises(ValueError, match='Bitiş tarihi başlangıç tarihinden önce'):
        plan_form_from_request({
            'action': 'add_income_plan',
            'name': 'Geçersiz plan',
            'category': 'Maaş',
            'amount': '1000',
            'installments': '2',
            'payment_day': '10',
            'start_date': '2026-08-20',
            'end_date': '2026-08-19',
            'plan_type': 'Dönemsel',
            'frequency': 'Aylık',
        })


@pytest.mark.regression
def test_plan_update_preserves_paid_period_and_rebuilds_remaining_periods(app):
    """Updating a plan must preserve paid history and regenerate only remaining periods."""
    with app.app_context():
        repo = FinancialRepository()
        plan = repo.add_recurring_plan(
            name='Maaş Emin',
            category='Maaş',
            amount=50000,
            installments=4,
            payment_day=10,
            start_date='2026-08-19',
            tenant_id='default',
            plan_type='Dönemsel',
            frequency='Aylık',
        )
        repo.create_payment(plan.id, 50000, '2026-09-10', 1, tenant_id='default')

        repo.update_recurring_plan(
            plan.id,
            'Maaş Emin',
            'Maaş',
            50000,
            4,
            10,
            start_date='2026-08-19',
            tenant_id='default',
            plan_type='Dönemsel',
            frequency='Aylık',
        )

        transactions = (
            Transaction.query.filter_by(source_id=plan.id, source_type='plan')
            .order_by(Transaction.installment_number)
            .all()
        )
        assert [(tx.installment_number, tx.status, tx.date) for tx in transactions] == [
            (1, 'Ödendi', '2026-09-10'),
            (2, 'Bekliyor', '2026-10-10'),
            (3, 'Bekliyor', '2026-11-10'),
            (4, 'Bekliyor', '2026-12-10'),
        ]
