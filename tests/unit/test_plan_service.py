"""
Unit Tests - Plan Service
Plan and payment calendar service tests
"""

from datetime import date, datetime, timedelta
from types import SimpleNamespace
from unittest.mock import Mock, patch

import pytest


@pytest.mark.unit
def test_plan_service_save_plan_syncs_occurrence_schedule(app):
    from flask import g

    from domain.planning.services.plan_service import PlanService

    financial_repository = Mock()
    catalog_repository = Mock()
    occurrence_service = Mock()
    created_plan = SimpleNamespace(id=101, tenant_id="default")
    financial_repository.add_recurring_plan.return_value = created_plan
    dto = SimpleNamespace(
        plan_id=None,
        name="Test plan",
        category="Maaş",
        amount=1000,
        installments=3,
        payment_day=10,
        note=None,
        start_date="2026-08-20",
        plan_type="Taksit",
        frequency="Aylık",
        end_date=None,
        target_asset_id=None,
        version=None,
    )

    with app.app_context():
        g.tenant_id = "default"
        result = PlanService(
            financial_repository=financial_repository,
            catalog_repository=catalog_repository,
            occurrence_service=occurrence_service,
        ).save_plan(dto)

    assert result == "Yeni plan başarıyla eklendi."
    occurrence_service.sync_plan.assert_called_once_with(created_plan, "default")


@pytest.mark.unit
def test_plan_service_payment_calendar_context():
    """Test payment_calendar_context returns correct data"""
    from domain.planning.services.plan_service import PlanService

    mock_financial_repo = Mock()
    mock_catalog_repo = Mock()
    service = PlanService(financial_repository=mock_financial_repo, catalog_repository=mock_catalog_repo)

    # Mock transactions
    mock_tx1 = Mock()
    mock_tx1.type = 'Gelir'
    mock_tx1.amount = 5000
    mock_tx1.status = 'Ödendi'

    mock_tx2 = Mock()
    mock_tx2.type = 'Gider'
    mock_tx2.amount = 1000
    mock_tx2.status = 'Ödendi'

    mock_financial_repo.list_transactions.return_value = [mock_tx1, mock_tx2]
    mock_financial_repo.pending_transactions_between.return_value = []

    result = service.payment_calendar_context()

    assert result['today_cash'] == 4000  # 5000 - 1000
    assert 'week_p' in result
    assert 'month_p' in result
    assert 'cal_year' in result
    assert 'cal_month' in result
    assert 'cal_month_name' in result
    assert 'today_iso' in result


@pytest.mark.unit
def test_plan_service_month_data():
    """Test month_data returns correct calendar data"""
    from domain.planning.services.plan_service import PlanService

    mock_financial_repo = Mock()
    mock_catalog_repo = Mock()
    service = PlanService(financial_repository=mock_financial_repo, catalog_repository=mock_catalog_repo)

    with patch('domain.planning.services.plan_service.get_calendar_month_data') as mock_get_data:
        mock_get_data.return_value = {'days': [1, 2, 3]}

        result = service.month_data(2024, 8)

        assert result['year'] == 2024
        assert result['month'] == 8
        assert result['month_name'] == 'Ağustos'
        assert 'today' in result
        assert 'days' in result


@pytest.mark.unit
def test_plan_service_daily_balance():
    """Test daily_balance returns correct balance data"""
    from domain.planning.services.plan_service import PlanService

    mock_financial_repo = Mock()
    mock_catalog_repo = Mock()
    service = PlanService(financial_repository=mock_financial_repo, catalog_repository=mock_catalog_repo)

    mock_financial_repo.list_transactions.return_value = []

    with patch('domain.planning.services.plan_service.calculate_monthly_daily_balance') as mock_calc:
        mock_calc.return_value = ([datetime(2024, 8, 1), datetime(2024, 8, 2)], [1000, 2000])

        with patch('domain.planning.services.plan_service.format_date') as mock_format:
            mock_format.side_effect = lambda d: d.strftime('%Y-%m-%d')

            result = service.daily_balance(2024, 8)

            assert result['year'] == 2024
            assert result['month'] == 8
            assert 'labels' in result
            assert 'data' in result


@pytest.mark.unit
def test_plan_service_add_payment_plan_not_found():
    """Test add_payment raises LookupError when plan not found"""
    from domain.planning.services.plan_service import PlanService

    mock_financial_repo = Mock()
    mock_catalog_repo = Mock()
    service = PlanService(financial_repository=mock_financial_repo, catalog_repository=mock_catalog_repo)

    mock_financial_repo.get_recurring_plan_for_tenant.return_value = None

    mock_dto = Mock()
    mock_dto.plan_id = 999
    mock_dto.amount = 1000
    mock_dto.payment_date = '2024-01-01'
    mock_dto.installment_number = 1
    mock_dto.notes = 'Test'

    with pytest.raises(LookupError) as exc_info:
        service.add_payment(mock_dto, 'tenant_123')

    assert "Plan bulunamadı." in str(exc_info.value)


@pytest.mark.unit
def test_plan_service_add_payment_invalid_installment():
    """Test add_payment raises ValueError for invalid installment number"""
    from domain.planning.services.plan_service import PlanService

    mock_financial_repo = Mock()
    mock_catalog_repo = Mock()
    service = PlanService(financial_repository=mock_financial_repo, catalog_repository=mock_catalog_repo)

    mock_plan = Mock()
    mock_plan.installments = 12
    mock_plan.plan_type = 'Taksit'
    mock_plan.target_asset_id = None

    mock_financial_repo.get_recurring_plan_for_tenant.return_value = mock_plan

    mock_dto = Mock()
    mock_dto.plan_id = 123
    mock_dto.amount = 1000
    mock_dto.payment_date = '2024-01-01'
    mock_dto.installment_number = 15  # Invalid: > 12
    mock_dto.notes = 'Test'

    with pytest.raises(ValueError) as exc_info:
        service.add_payment(mock_dto, 'tenant_123')

    assert "Taksit numarası" in str(exc_info.value)


@pytest.mark.unit
def test_plan_service_add_payment_dca_plan():
    """Test add_payment handles DCA plan with asset transfer"""
    from domain.planning.services.plan_service import PlanService

    mock_financial_repo = Mock()
    mock_catalog_repo = Mock()
    service = PlanService(financial_repository=mock_financial_repo, catalog_repository=mock_catalog_repo)

    mock_plan = Mock()
    mock_plan.installments = 0
    mock_plan.plan_type = 'DCA'
    mock_plan.target_asset_id = 'asset_123'

    mock_financial_repo.get_recurring_plan_for_tenant.return_value = mock_plan

    mock_dto = Mock()
    mock_dto.plan_id = 123
    mock_dto.amount = 1000
    mock_dto.payment_date = '2024-01-01'
    mock_dto.installment_number = 1
    mock_dto.notes = 'Test'

    with patch('domain.transactions.services.financial_ledger.transfer_cash_to_asset') as mock_transfer:
        mock_financial_repo.create_payment.return_value = None

        service.add_payment(mock_dto, 'tenant_123')

        mock_transfer.assert_called_once()
        mock_financial_repo.create_payment.assert_called_once()


@pytest.mark.unit
def test_plan_service_plans_context():
    """Test plans_context returns correct plan data"""
    from domain.planning.services.plan_service import PlanService

    mock_financial_repo = Mock()
    mock_catalog_repo = Mock()
    service = PlanService(financial_repository=mock_financial_repo, catalog_repository=mock_catalog_repo)

    # Mock plans
    mock_income_plan = Mock()
    mock_income_plan.plan_type = 'Dönemsel'
    mock_income_plan.amount = 5000

    mock_expense_plan = Mock()
    mock_expense_plan.plan_type = 'Abonelik'
    mock_expense_plan.amount = 1000

    mock_investment_plan = Mock()
    mock_investment_plan.plan_type = 'DCA'
    mock_investment_plan.amount = 2000

    mock_financial_repo.list_recurring_plans.side_effect = [
        [mock_income_plan],  # Gelir
        [mock_expense_plan],  # Gider
        [mock_investment_plan],  # Yatırım
    ]

    mock_catalog_repo.list_categories_by_type.return_value = []

    result = service.plans_context('tenant_123')

    assert result['income_total'] == 5000
    assert result['expense_total'] == 1000
    assert result['dca_total'] == 2000
    assert result['net_total'] == 4000
    assert result['plan_count'] == 3
    assert 'subscription_plans' in result
    assert 'installment_plans' in result
    assert 'dca_plans' in result
    assert 'periodic_plans' in result


@pytest.mark.unit
def test_plan_service_plan_detail_is_tenant_scoped_and_read_only():
    """Detail insight reads one tenant's plan and never synchronises its schedule."""
    from domain.planning.services.plan_service import PlanService

    financial_repository = Mock()
    catalog_repository = Mock()
    occurrence_repository = Mock()
    occurrence_service = SimpleNamespace(repository=occurrence_repository)
    plan = SimpleNamespace(
        id=42,
        tenant_id='tenant_a',
        name='Maaş',
        category='Gelir',
        flow_type='Gelir',
        amount='12500.00',
        frequency='Aylık',
        plan_type='Dönemsel',
        installments=0,
        payment_day=1,
        start_date='2026-08-25',
        end_date=None,
        status='Aktif',
        note='Aylık maaş',
        target_asset_id=None,
    )
    today = date.today()
    occurrence_repository.list_for_plan.return_value = [
        SimpleNamespace(
            id=501,
            plan_id=42,
            occurrence_number=1,
            scheduled_date=(today - timedelta(days=1)).isoformat(),
            status='paid',
            amount='12500.00',
            transaction_id=701,
        ),
        SimpleNamespace(
            id=502,
            plan_id=42,
            occurrence_number=2,
            scheduled_date=(today + timedelta(days=3)).isoformat(),
            status='scheduled',
            amount='12500.00',
            transaction_id=None,
        ),
        SimpleNamespace(
            id=503,
            plan_id=42,
            occurrence_number=3,
            scheduled_date=(today + timedelta(days=10)).isoformat(),
            status='scheduled',
            amount='12500.00',
            transaction_id=None,
        ),
    ]
    financial_repository.get_recurring_plan_for_tenant.return_value = plan

    result = PlanService(
        financial_repository=financial_repository,
        catalog_repository=catalog_repository,
        occurrence_service=occurrence_service,
    ).plan_detail_context(42, 'tenant_a')

    financial_repository.get_recurring_plan_for_tenant.assert_called_once_with(42, 'tenant_a')
    occurrence_repository.list_for_plan.assert_called_once_with(42, 'tenant_a')
    assert result['plan']['tenant_id'] == 'tenant_a'
    assert result['summary'] == {'total': 3, 'scheduled': 2, 'paid': 1, 'skipped': 0, 'cancelled': 0}
    assert result['next_occurrence']['id'] == 502
    assert result['next_occurrence']['occurrence_number'] == 2
    occurrence_repository.get_or_create_occurrences.assert_not_called()
    assert not hasattr(occurrence_service, 'sync_plan')


@pytest.mark.unit
def test_upcoming_occurrences_are_tenant_scoped_and_deterministic(app):
    from domain.planning.services.occurrence_repository import OccurrenceRepository
    from models import PlanOccurrence, RecurringPlan, Tenant, db

    today = date.today()
    with app.app_context():
        tenant_a = Tenant(id='tenant-upcoming-a', name='Upcoming A')
        tenant_b = Tenant(id='tenant-upcoming-b', name='Upcoming B')
        db.session.add_all([tenant_a, tenant_b])
        db.session.flush()
        plans = [
            RecurringPlan(
                name='Plan A1', category='Gider', flow_type='Gider', amount=100,
                installments=12, payment_day=1, start_date=today.isoformat(),
                tenant_id=tenant_a.id, plan_type='Taksit', frequency='Aylık', status='Aktif',
            ),
            RecurringPlan(
                name='Plan A2', category='Gelir', flow_type='Gelir', amount=200,
                installments=12, payment_day=1, start_date=today.isoformat(),
                tenant_id=tenant_a.id, plan_type='Taksit', frequency='Aylık', status='Aktif',
            ),
            RecurringPlan(
                name='Plan B1', category='Gider', flow_type='Gider', amount=300,
                installments=12, payment_day=1, start_date=today.isoformat(),
                tenant_id=tenant_b.id, plan_type='Taksit', frequency='Aylık', status='Aktif',
            ),
        ]
        db.session.add_all(plans)
        db.session.flush()
        db.session.add_all([
            PlanOccurrence(plan_id=plans[0].id, occurrence_number=1, scheduled_date=today.isoformat(), status='scheduled', amount=100, tenant_id=tenant_a.id),
            PlanOccurrence(plan_id=plans[1].id, occurrence_number=1, scheduled_date=today.isoformat(), status='scheduled', amount=200, tenant_id=tenant_a.id),
            PlanOccurrence(plan_id=plans[0].id, occurrence_number=2, scheduled_date=(today - timedelta(days=1)).isoformat(), status='scheduled', amount=100, tenant_id=tenant_a.id),
            PlanOccurrence(plan_id=plans[0].id, occurrence_number=3, scheduled_date=today.isoformat(), status='paid', amount=100, tenant_id=tenant_a.id),
            PlanOccurrence(plan_id=plans[2].id, occurrence_number=1, scheduled_date=today.isoformat(), status='scheduled', amount=300, tenant_id=tenant_b.id),
            PlanOccurrence(plan_id=plans[0].id, occurrence_number=4, scheduled_date=(today + timedelta(days=10)).isoformat(), status='scheduled', amount=100, tenant_id=tenant_a.id),
        ])
        db.session.commit()
        before = db.session.query(PlanOccurrence).count()

        repository = OccurrenceRepository()
        through_date = today + timedelta(days=6)
        rows = repository.list_upcoming(tenant_a.id, from_date=today, through_date=through_date, limit=50)
        count = repository.count_upcoming_for_tenant(tenant_a.id, from_date=today, through_date=through_date)

        assert [row.tenant_id for row in rows] == [tenant_a.id, tenant_a.id]
        assert [row.status for row in rows] == ['scheduled', 'scheduled']
        assert [row.scheduled_date for row in rows] == [today.isoformat(), today.isoformat()]
        assert [row.id for row in rows] == sorted(row.id for row in rows)
        assert count == 2
        assert db.session.query(PlanOccurrence).count() == before


@pytest.mark.unit
def test_plan_detail_api_contract_and_tenant_boundary(app, authenticated_client):
    from models import PlanOccurrence, RecurringPlan, Tenant, db

    today = date.today()
    with app.app_context():
        other_tenant = Tenant(id='tenant-detail-other', name='Detail Other')
        db.session.add(other_tenant)
        db.session.flush()
        visible_plan = RecurringPlan(
            name='Görünür plan', category='Gider', flow_type='Gider', amount=75,
            installments=3, payment_day=25, start_date=today.isoformat(),
            tenant_id='default', plan_type='Taksit', frequency='Aylık', status='Aktif',
        )
        hidden_plan = RecurringPlan(
            name='Başka tenant planı', category='Gider', flow_type='Gider', amount=90,
            installments=3, payment_day=25, start_date=today.isoformat(),
            tenant_id=other_tenant.id, plan_type='Taksit', frequency='Aylık', status='Aktif',
        )
        db.session.add_all([visible_plan, hidden_plan])
        db.session.flush()
        db.session.add(PlanOccurrence(
            plan_id=visible_plan.id,
            occurrence_number=1,
            scheduled_date=(today + timedelta(days=2)).isoformat(),
            status='scheduled',
            amount=75,
            tenant_id='default',
        ))
        db.session.commit()
        before = db.session.query(PlanOccurrence).count()
        visible_plan_id = visible_plan.id
        hidden_plan_id = hidden_plan.id

        response = authenticated_client.get(f'/api/plans/{visible_plan_id}')
        hidden_response = authenticated_client.get(f'/api/plans/{hidden_plan_id}')

        assert response.status_code == 200
        payload = response.get_json()
        assert payload['success'] is True
        assert payload['data']['plan']['id'] == visible_plan_id
        assert payload['data']['plan']['tenant_id'] == 'default'
        assert payload['data']['summary']['scheduled'] == 1
        assert payload['data']['plan']['months_remaining'] is not None
        assert hidden_response.status_code == 404
        assert db.session.query(PlanOccurrence).count() == before


@pytest.mark.unit
def test_canonical_plan_months_remaining_and_is_active():
    from decimal import Decimal

    from dateutil.relativedelta import relativedelta

    from domain.planning.models.plan_contracts import CanonicalPlan, PlanFlow, PlanLifecycle, PlanStatus

    today = date.today()


    # 1. Süresiz plan (Abonelik) -> None (sonsuz)
    sub_plan = CanonicalPlan(
        id=1, tenant_id='t1', name='Spotify', category='Eğlence',
        flow=PlanFlow.EXPENSE, amount=Decimal('59.99'), frequency='Aylık',
        lifecycle=PlanLifecycle.INDEFINITE, start_date=today, end_date=None,
        occurrence_limit=None, payment_day=1, status=PlanStatus.ACTIVE,
    )
    assert sub_plan.is_active is True
    assert sub_plan.months_remaining is None

    # 2. Tamamlanmış plan -> 0, is_active=False
    done_plan = CanonicalPlan(
        id=2, tenant_id='t1', name='Eski Kredi', category='Kredi',
        flow=PlanFlow.EXPENSE, amount=Decimal('1000'), frequency='Aylık',
        lifecycle=PlanLifecycle.INSTALLMENT, start_date=today - timedelta(days=400),
        end_date=None, occurrence_limit=12, payment_day=5, status=PlanStatus.COMPLETED,
    )
    assert done_plan.is_active is False
    assert done_plan.months_remaining == 0

    # 3. İptal edilmiş plan -> 0, is_active=False
    cancelled_plan = CanonicalPlan(
        id=3, tenant_id='t1', name='İptal Plan', category='Diğer',
        flow=PlanFlow.EXPENSE, amount=Decimal('500'), frequency='Aylık',
        lifecycle=PlanLifecycle.INSTALLMENT, start_date=today,
        end_date=None, occurrence_limit=6, payment_day=15, status=PlanStatus.CANCELLED,
    )
    assert cancelled_plan.is_active is False
    assert cancelled_plan.months_remaining == 0

    # 4. Bitiş tarihli plan (gelecek) -> ay farkı
    future_end = date(today.year, today.month, 1) + relativedelta(months=5)
    end_dated_plan = CanonicalPlan(
        id=4, tenant_id='t1', name='Kira', category='Kira',
        flow=PlanFlow.EXPENSE, amount=Decimal('15000'), frequency='Aylık',
        lifecycle=PlanLifecycle.END_DATED, start_date=today,
        end_date=future_end, occurrence_limit=None, payment_day=1, status=PlanStatus.ACTIVE,
    )
    assert end_dated_plan.months_remaining == 5

    # 5. Taksitli plan (12 taksit, 2 ay önce başlamış) -> 10 taksit kaldı
    start_2_months_ago = date(today.year, today.month, 1) - relativedelta(months=2)
    inst_plan = CanonicalPlan(
        id=5, tenant_id='t1', name='Telefon', category='Elektronik',
        flow=PlanFlow.EXPENSE, amount=Decimal('3000'), frequency='Aylık',
        lifecycle=PlanLifecycle.INSTALLMENT, start_date=start_2_months_ago,
        end_date=None, occurrence_limit=12, payment_day=15, status=PlanStatus.ACTIVE,
    )
    assert inst_plan.months_remaining == 10



@pytest.mark.unit
def test_canonical_plan_remaining_total_and_countdown():
    from decimal import Decimal

    from dateutil.relativedelta import relativedelta

    from domain.planning.models.plan_contracts import CanonicalPlan, PlanFlow, PlanLifecycle, PlanStatus

    today = date.today()
    # 1. 12 taksitli plan, 2 ay önce başlamış -> 10 taksit kaldı, tutar 2500 -> kalan toplam 25000
    start_2_mo = date(today.year, today.month, 1) - relativedelta(months=2)
    plan = CanonicalPlan(
        id=10, tenant_id='t1', name='Kredi', category='Kredi',
        flow=PlanFlow.EXPENSE, amount=Decimal('2500.00'), frequency='Aylık',
        lifecycle=PlanLifecycle.INSTALLMENT, start_date=start_2_mo,
        end_date=None, occurrence_limit=12, payment_day=today.day, status=PlanStatus.ACTIVE,
    )
    assert plan.months_remaining == 10
    assert plan.remaining_total_amount == Decimal('25000.00')

    # Countdown bugün için
    countdown = plan.payment_countdown
    assert countdown is not None
    assert countdown['days'] == 0
    assert 'Bugün' in countdown['label']

    # Süresiz plan
    sub = CanonicalPlan(
        id=11, tenant_id='t1', name='Spotify', category='Abonelik',
        flow=PlanFlow.EXPENSE, amount=Decimal('50.00'), frequency='Aylık',
        lifecycle=PlanLifecycle.INDEFINITE, start_date=today,
        end_date=None, occurrence_limit=None, payment_day=today.day, status=PlanStatus.ACTIVE,
    )
    assert sub.remaining_total_amount is None


@pytest.mark.unit
def test_plan_service_save_plan_passes_status_on_update(app):
    from flask import g

    from domain.planning.services.plan_service import PlanService

    mock_repo = Mock()
    mock_catalog = Mock()
    mock_occurrence = Mock()
    updated_plan = SimpleNamespace(id=5, tenant_id='default', status='Duraklatıldı')
    mock_repo.update_recurring_plan.return_value = updated_plan

    dto = SimpleNamespace(
        plan_id=5,
        name='Test Plan',
        category='Kira',
        amount=10000,
        installments=12,
        payment_day=1,
        note=None,
        start_date='2026-01-01',
        plan_type='Taksit',
        frequency='Aylık',
        end_date=None,
        target_asset_id=None,
        version=1,
        status='Duraklatıldı',
    )

    with app.app_context():
        g.tenant_id = 'default'
        svc = PlanService(financial_repository=mock_repo, catalog_repository=mock_catalog, occurrence_service=mock_occurrence)
        res = svc.save_plan(dto)

    assert res == 'Plan başarıyla güncellendi.'
    mock_repo.update_recurring_plan.assert_called_once()
    assert mock_repo.update_recurring_plan.call_args[1].get('status') == 'Duraklatıldı'


@pytest.mark.unit
def test_canonical_plan_countdown_month_wrapping_and_tones():
    from decimal import Decimal
    from domain.planning.models.plan_contracts import CanonicalPlan, PlanFlow, PlanLifecycle, PlanStatus

    today = date.today()

    # Plan with payment_day = today.day (today)
    p_today = CanonicalPlan(
        id=20, tenant_id='t1', name='Bugün Ödeme', category='Kira',
        flow=PlanFlow.EXPENSE, amount=Decimal('5000'), frequency='Aylık',
        lifecycle=PlanLifecycle.INSTALLMENT, start_date=today,
        end_date=None, occurrence_limit=12, payment_day=today.day, status=PlanStatus.ACTIVE,
    )
    cd_today = p_today.payment_countdown
    assert cd_today is not None
    assert cd_today['days'] == 0
    assert cd_today['tone'] == 'today'
    assert 'bg-rose-100' in cd_today['badge_class']

    # Plan whose payment_day already passed this month (e.g. today.day + 1 is next month or payment_day was day 1 and today is day 20)
    past_day = 1 if today.day > 1 else 28
    p_next_month = CanonicalPlan(
        id=21, tenant_id='t1', name='Gelecek Ay Ödeme', category='Abonelik',
        flow=PlanFlow.EXPENSE, amount=Decimal('100'), frequency='Aylık',
        lifecycle=PlanLifecycle.INDEFINITE, start_date=today,
        end_date=None, occurrence_limit=None, payment_day=past_day, status=PlanStatus.ACTIVE,
    )
    cd_next = p_next_month.payment_countdown
    assert cd_next is not None
    assert cd_next['days'] >= 0  # Crucial: never negative!
    assert 'önceydi' not in cd_next['label']
    assert 'badge_class' in cd_next

    # Paused plan
    p_paused = CanonicalPlan(
        id=22, tenant_id='t1', name='Duraklatılmış Plan', category='Diğer',
        flow=PlanFlow.EXPENSE, amount=Decimal('200'), frequency='Aylık',
        lifecycle=PlanLifecycle.INDEFINITE, start_date=today,
        end_date=None, occurrence_limit=None, payment_day=15, status=PlanStatus.PAUSED,
    )
    cd_paused = p_paused.payment_countdown
    assert cd_paused is not None
    assert cd_paused['tone'] == 'paused'
    assert 'Duraklatıldı' in cd_paused['label']

    # Completed/Cancelled plan
    p_done = CanonicalPlan(
        id=23, tenant_id='t1', name='Biten Plan', category='Diğer',
        flow=PlanFlow.EXPENSE, amount=Decimal('200'), frequency='Aylık',
        lifecycle=PlanLifecycle.INSTALLMENT, start_date=today,
        end_date=None, occurrence_limit=6, payment_day=15, status=PlanStatus.COMPLETED,
    )
    assert p_done.payment_countdown is None


@pytest.mark.unit
def test_canonical_plan_paid_occurrences_override_and_weekly():
    from decimal import Decimal
    from domain.planning.models.plan_contracts import CanonicalPlan, PlanFlow, PlanLifecycle, PlanStatus

    today = date.today()

    # 1. 12 taksitli plan, paid_occurrences_count = 5 -> kalan 7
    p_paid = CanonicalPlan(
        id=30, tenant_id='t1', name='Kredi', category='Kredi',
        flow=PlanFlow.EXPENSE, amount=Decimal('1000.00'), frequency='Aylık',
        lifecycle=PlanLifecycle.INSTALLMENT, start_date=today,
        end_date=None, occurrence_limit=12, payment_day=1, status=PlanStatus.ACTIVE,
        paid_occurrences_count=5,
    )
    assert p_paid.months_remaining == 7
    assert p_paid.remaining_total_amount == Decimal('7000.00')

    # 2. Haftalık plan with end_date 4 weeks ahead
    p_weekly = CanonicalPlan(
        id=31, tenant_id='t1', name='Haftalık Harçlık', category='Harçlık',
        flow=PlanFlow.EXPENSE, amount=Decimal('250.00'), frequency='Haftalık',
        lifecycle=PlanLifecycle.END_DATED, start_date=today,
        end_date=today + timedelta(days=28), occurrence_limit=None, payment_day=1, status=PlanStatus.ACTIVE,
    )
    assert p_weekly.months_remaining == 4

    # 3. Future start date
    p_future = CanonicalPlan(
        id=32, tenant_id='t1', name='Gelecek Taksit', category='Diğer',
        flow=PlanFlow.EXPENSE, amount=Decimal('500.00'), frequency='Aylık',
        lifecycle=PlanLifecycle.INSTALLMENT, start_date=today + timedelta(days=60),
        end_date=None, occurrence_limit=10, payment_day=15, status=PlanStatus.ACTIVE,
    )
    assert p_future.months_remaining == 10


@pytest.mark.unit
def test_occurrence_repository_cancels_orphaned_occurrences_on_installment_reduction(app):
    from domain.planning.services.occurrence_repository import OccurrenceRepository
    from models import PlanOccurrence, RecurringPlan, Tenant, db

    today = date.today()
    with app.app_context():
        tenant = Tenant(id='tenant-orphan-test', name='Orphan Test')
        db.session.add(tenant)
        db.session.flush()

        plan = RecurringPlan(
            name='Kredi Planı', category='Kredi', flow_type='Gider', amount=1000,
            installments=4, payment_day=15, start_date=today.isoformat(),
            tenant_id=tenant.id, plan_type='Taksit', frequency='Aylık', status='Aktif',
        )
        db.session.add(plan)
        db.session.flush()

        repo = OccurrenceRepository()
        # Initial 4 occurrences
        initial_occurrences = repo.get_or_create_occurrences(plan, tenant.id)
        assert len(initial_occurrences) == 4
        assert all(occ.status == 'scheduled' for occ in initial_occurrences)

        # Now simulate reducing installments to 2
        plan.installments = 2
        updated_occurrences = repo.get_or_create_occurrences(plan, tenant.id)

        all_rows = db.session.query(PlanOccurrence).filter_by(plan_id=plan.id).order_by(PlanOccurrence.occurrence_number).all()
        assert len(all_rows) == 4
        assert all_rows[0].status == 'scheduled'
        assert all_rows[1].status == 'scheduled'
        assert all_rows[2].status == 'cancelled'
        assert all_rows[3].status == 'cancelled'
        assert 'iptal edildi' in (all_rows[2].notes or '')


@pytest.mark.unit
def test_create_payment_auto_creates_missing_plan_occurrence(app):
    from models import Category, Payment, PlanOccurrence, RecurringPlan, Tenant, db
    from repositories.financial_repository import FinancialRepository

    today = date.today().isoformat()
    with app.app_context():
        tenant = Tenant(id='tenant-auto-occ', name='Auto Occ')
        cat = Category(name='Genel Kategori', type='Gider')
        db.session.add_all([tenant, cat])
        db.session.flush()

        plan = RecurringPlan(
            name='Plansız Taksit', category='Genel Kategori', flow_type='Gider', amount=500,
            installments=3, payment_day=10, start_date=today,
            tenant_id=tenant.id, plan_type='Taksit', frequency='Aylık', status='Aktif',
        )
        db.session.add(plan)
        db.session.commit()

        # No PlanOccurrence records were generated yet
        assert db.session.query(PlanOccurrence).filter_by(plan_id=plan.id).count() == 0

        # Create payment for installment 1
        fin_repo = FinancialRepository()
        payment = fin_repo.create_payment(
            plan_id=plan.id,
            amount=500,
            payment_date=today,
            installment_number=1,
            notes='Test ödeme',
            tenant_id=tenant.id,
        )

        assert payment is not None
        # Verify PlanOccurrence was automatically created and marked paid
        occ = db.session.query(PlanOccurrence).filter_by(plan_id=plan.id, occurrence_number=1).first()
        assert occ is not None
        assert occ.status == 'paid'
        assert occ.transaction_id == payment.transaction_id


@pytest.mark.unit
def test_recurring_plan_optimistic_concurrency_error(app):
    from domain.transactions.services.financial_ledger import OptimisticConcurrencyError
    from models import Category, RecurringPlan, Tenant, db
    from repositories.financial_repository import FinancialRepository

    today = date.today().isoformat()
    with app.app_context():
        tenant = Tenant(id='tenant-concurr-test', name='Concurrency Test')
        cat = Category(name='Kira Kategorisi', type='Gider')
        db.session.add_all([tenant, cat])
        db.session.flush()

        plan = RecurringPlan(
            name='Kira', category='Kira Kategorisi', flow_type='Gider', amount=10000,
            installments=12, payment_day=1, start_date=today,
            tenant_id=tenant.id, plan_type='Taksit', frequency='Aylık', status='Aktif',
        )
        db.session.add(plan)
        db.session.commit()

        # plan.version is 1
        assert plan.version == 1

        fin_repo = FinancialRepository()
        with pytest.raises(OptimisticConcurrencyError):
            fin_repo.update_recurring_plan(
                plan_id=plan.id,
                name='Kira Güncel',
                category='Kira Kategorisi',
                amount=12000,
                installments=12,
                payment_day=1,
                tenant_id=tenant.id,
                version=999,  # Stale version!
            )


@pytest.mark.unit
def test_mark_occurrence_paid_executes_dca_transfer(app):
    from decimal import Decimal
    from unittest.mock import patch
    from domain.transactions.services.ledger_adjustment_service import mark_occurrence_paid
    from models import Category, PlanOccurrence, RecurringPlan, Tenant, db

    today = date.today().isoformat()
    with app.app_context():
        tenant = Tenant(id='tenant-dca-occ', name='DCA Occ')
        cat = Category(name='Fon Kategorisi', type='Yatırım')
        db.session.add_all([tenant, cat])
        db.session.flush()

        plan = RecurringPlan(
            name='Aylık Fon Alımı', category='Fon Kategorisi', flow_type='Yatırım', amount=1500,
            installments=0, payment_day=5, start_date=today,
            tenant_id=tenant.id, plan_type='DCA', frequency='Aylık', status='Aktif',
            target_asset_id=42,
        )
        db.session.add(plan)
        db.session.flush()

        occ = PlanOccurrence(
            plan_id=plan.id,
            occurrence_number=1,
            scheduled_date=today,
            status='scheduled',
            amount=1500,
            tenant_id=tenant.id,
        )
        db.session.add(occ)
        db.session.commit()

        with patch('domain.transactions.services.ledger_position_service.transfer_cash_to_asset') as mock_transfer:
            payment = mark_occurrence_paid(
                occurrence_id=occ.id,
                payment_dto={'amount': 1500, 'payment_date': today, 'notes': 'DCA ödeme'},
                tenant_id=tenant.id,
            )
            assert payment is not None
            mock_transfer.assert_called_once_with(42, Decimal('1500'), today, tenant.id, skip_cash_tx=True)
            db.session.refresh(occ)
            assert occ.status == 'paid'
            assert occ.transaction_id == payment.transaction_id


@pytest.mark.unit
def test_occurrence_calculator_rolling_horizon_for_indefinite_plans():
    """Verify indefinite plans generate rolling occurrences covering today + 3 months."""
    from decimal import Decimal
    from domain.planning.models.plan_contracts import CanonicalPlan, PlanFlow, PlanLifecycle, PlanStatus
    from domain.planning.services.occurrence_service import OccurrenceCalculator

    ref_today = date(2026, 10, 12)
    # 1. Indefinite subscription plan
    indefinite_plan = CanonicalPlan(
        id=501,
        tenant_id="tenant-rolling",
        name="Spotify Abonelik",
        category="Abonelik",
        flow=PlanFlow.EXPENSE,
        amount=Decimal("100"),
        frequency="Aylık",
        lifecycle=PlanLifecycle.INDEFINITE,
        start_date=date(2026, 8, 1),
        end_date=None,
        occurrence_limit=None,
        payment_day=1,
        status=PlanStatus.ACTIVE,
    )
    occurrences = OccurrenceCalculator.generate(indefinite_plan, today=ref_today)
    assert len(occurrences) >= 6  # Aug, Sep, Oct, Nov, Dec 2026, Jan 2027
    dates = [occ.scheduled_date.isoformat() for occ in occurrences]
    assert "2026-08-01" in dates
    assert "2026-10-01" in dates
    assert "2027-01-01" in dates

    # 2. Finite plan strictly respects occurrence limit
    finite_plan = CanonicalPlan(
        id=502,
        tenant_id="tenant-rolling",
        name="Kredi",
        category="Kredi",
        flow=PlanFlow.EXPENSE,
        amount=Decimal("1000"),
        frequency="Aylık",
        lifecycle=PlanLifecycle.INSTALLMENT,
        start_date=date(2026, 8, 1),
        end_date=None,
        occurrence_limit=3,
        payment_day=1,
        status=PlanStatus.ACTIVE,
    )
    finite_occs = OccurrenceCalculator.generate(finite_plan, today=ref_today)
    assert len(finite_occs) == 3


@pytest.mark.unit
def test_occurrence_repository_ensure_rolling_occurrences_for_active_plans(app):
    """Verify OccurrenceRepository automatically extends scheduled occurrences for active rolling plans."""
    from domain.planning.services.occurrence_repository import OccurrenceRepository
    from models import Category, RecurringPlan, Tenant, db

    with app.app_context():
        tenant = Tenant(id="tenant-rolling-repo", name="Rolling Repo")
        cat = Category(name="Müzik", type="Gider")
        db.session.add_all([tenant, cat])
        db.session.flush()

        plan = RecurringPlan(
            name="YouTube Premium",
            category="Müzik",
            flow_type="Gider",
            amount=80,
            installments=0,
            payment_day=15,
            start_date="2026-08-15",
            tenant_id=tenant.id,
            plan_type="Abonelik",
            frequency="Aylık",
            status="Aktif",
        )
        db.session.add(plan)
        db.session.commit()

        repo = OccurrenceRepository()
        # Initial ensure should generate rolling occurrences
        updated = repo.ensure_rolling_occurrences_for_active_plans(tenant_id=tenant.id)
        assert updated >= 1

        occs = repo.list_for_plan(plan.id, tenant_id=tenant.id)
        assert len(occs) >= 3

        # Second call should be a no-op (already has future horizon)
        second_updated = repo.ensure_rolling_occurrences_for_active_plans(tenant_id=tenant.id)
        assert second_updated == 0


@pytest.mark.unit
def test_reporting_repository_consolidates_plan_occurrences_in_calendar(app):
    """Verify ReportingRepository.get_calendar_month_data includes scheduled PlanOccurrences."""
    from repositories.reporting_repository import ReportingRepository
    from models import Category, PlanOccurrence, RecurringPlan, Tenant, db

    with app.app_context():
        tenant = Tenant(id="tenant-cal-consol", name="Cal Consol")
        cat = Category(name="Spor", type="Gider")
        db.session.add_all([tenant, cat])
        db.session.flush()

        plan = RecurringPlan(
            name="Gym Üyeliği",
            category="Spor",
            flow_type="Gider",
            amount=500,
            installments=12,
            payment_day=20,
            start_date="2026-11-01",
            tenant_id=tenant.id,
            plan_type="Taksit",
            frequency="Aylık",
            status="Aktif",
        )
        db.session.add(plan)
        db.session.flush()

        # Pure PlanOccurrence with no transaction record in November 2026
        occ = PlanOccurrence(
            plan_id=plan.id,
            occurrence_number=1,
            scheduled_date="2026-11-20",
            status="scheduled",
            amount=500,
            tenant_id=tenant.id,
            transaction_id=None,
        )
        db.session.add(occ)
        db.session.commit()

        repo = ReportingRepository()
        month_data = repo.get_calendar_month_data(year=2026, month=11, tenant_id=tenant.id)
        assert "2026-11-20" in month_data
        day_entry = month_data["2026-11-20"]
        assert len(day_entry["expense"]) == 1
        item = day_entry["expense"][0]
        assert item["description"] == "Gym Üyeliği (1. Taksit/Dönem)"
        assert item["amount"] == 500.0
        assert item["origin"] == "plan"
        assert day_entry["expense_total"] == 500.0
        assert day_entry["net"] == -500.0


def test_payment_calendar_context_totals(app):
    from decimal import Decimal
    from domain.planning.services.plan_service import PlanService

    with app.app_context():
        financial_repository = Mock()
        financial_repository.list_transactions.return_value = []
        financial_repository.pending_transactions_between.return_value = [
            SimpleNamespace(amount=Decimal("150.00")),
            SimpleNamespace(amount=Decimal("250.00")),
        ]
        service = PlanService(financial_repository=financial_repository)
        now = datetime(2026, 10, 12, 10, 0, 0)
        ctx = service.payment_calendar_context(now=now)
        assert ctx["week_total"] == Decimal("400.00")
        assert ctx["month_total"] == Decimal("400.00")
        assert ctx["cal_year"] == 2026
        assert ctx["cal_month"] == 10


def test_occurrence_calculator_until_date_horizon():
    from decimal import Decimal
    from domain.planning.models.plan_contracts import CanonicalPlan, PlanFlow, PlanLifecycle, PlanStatus
    from domain.planning.services.occurrence_service import OccurrenceCalculator

    plan = CanonicalPlan(
        id=99,
        tenant_id="test-tenant",
        name="Abonelik",
        category="Yazılım",
        flow=PlanFlow.EXPENSE,
        amount=Decimal("100"),
        frequency="Aylık",
        lifecycle=PlanLifecycle.INDEFINITE,
        start_date=date(2026, 1, 1),
        end_date=None,
        occurrence_limit=None,
        payment_day=15,
        status=PlanStatus.ACTIVE,
    )
    ref_today = date(2026, 1, 1)
    target_date = date(2026, 7, 31)
    occs = OccurrenceCalculator.generate(plan, today=ref_today, until_date=target_date)
    dates = [o.scheduled_date for o in occs]
    assert len(dates) >= 7
    assert date(2026, 7, 15) in dates





