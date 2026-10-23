"""Unit tests for ReminderService, UserReminder model, and ReminderApplicationService."""

from datetime import date
from decimal import Decimal
from unittest.mock import MagicMock

import pytest

from application.analysis.reminder_application import ReminderApplicationService
from domain.analysis.services.reminder_service import ReminderService
from domain.transactions.models.transaction_models import UserReminder
from repositories.reminder_repository import ReminderRepository


@pytest.mark.unit
def test_reminder_service_validation():
    """Test validation rules for reminder creation/updating."""
    # Empty title
    valid, err = ReminderService.validate_reminder("", "Aylık", due_day=5)
    assert not valid
    assert "başlığı zorunludur" in err

    # Invalid frequency
    valid, err = ReminderService.validate_reminder("Test", "Haftalık")
    assert not valid
    assert "Geçersiz sıklık" in err

    # Monthly without valid day
    valid, err = ReminderService.validate_reminder("Kira", "Aylık", due_day=0)
    assert not valid
    assert "1-31" in err

    valid, err = ReminderService.validate_reminder("Kira", "Aylık", due_day=15)
    assert valid
    assert err is None

    # Yearly validation
    valid, err = ReminderService.validate_reminder("Doğum Günü", "Yıllık", due_day=15, due_month=0)
    assert not valid
    assert "1-12" in err

    valid, err = ReminderService.validate_reminder("Doğum Günü", "Yıllık", due_day=24, due_month=10)
    assert valid

    # One-off validation
    valid, err = ReminderService.validate_reminder("Borç", "Tek Seferlik", due_date="")
    assert not valid

    valid, err = ReminderService.validate_reminder("Borç", "Tek Seferlik", due_date="invalid-date")
    assert not valid

    valid, err = ReminderService.validate_reminder("Borç", "Tek Seferlik", due_date="2026-11-20")
    assert valid


@pytest.mark.unit
def test_reminder_service_due_status_calculation():
    """Test days remaining calculation and badge generation."""
    ref_date = date(2026, 10, 23)

    # 1. Monthly test: Target day is 23 (today)
    status_today = ReminderService.calculate_due_status('Aylık', due_day=23, reference_date=ref_date)
    assert status_today['days_remaining'] == 0
    assert status_today['badge_text'] == 'Bugün!'
    assert status_today['is_urgent'] is True

    # 2. Monthly test: Target day is 24 (tomorrow)
    status_tomorrow = ReminderService.calculate_due_status('Aylık', due_day=24, reference_date=ref_date)
    assert status_tomorrow['days_remaining'] == 1
    assert status_tomorrow['badge_text'] == 'Yarın'

    # 3. Monthly test: Target day was 10 (passed this month -> targets next month Nov 10)
    status_next_month = ReminderService.calculate_due_status('Aylık', due_day=10, reference_date=ref_date)
    # From Oct 23 to Nov 10 is 18 days
    assert status_next_month['days_remaining'] == 18

    # 4. Yearly test: Target is Dec 1st
    status_yearly = ReminderService.calculate_due_status('Yıllık', due_day=1, due_month=12, reference_date=ref_date)
    assert status_yearly['days_remaining'] == (date(2026, 12, 1) - ref_date).days

    # 5. Completed test
    status_done = ReminderService.calculate_due_status('Aylık', due_day=23, is_completed=True, reference_date=ref_date)
    assert status_done['badge_text'] == 'Tamamlandı ✓'
    assert status_done['badge_color'] == 'emerald'


@pytest.mark.unit
def test_user_reminder_model_properties():
    """Test UserReminder model helper properties."""
    reminder = UserReminder(
        tenant_id="tenant_1",
        title="Eşimin Doğum Günü",
        category="Doğum Günü",
        frequency="Yıllık",
        due_day=24,
        due_month=10,
        amount=Decimal("500.00"),
        note="Pasta al",
        document_url="/static/uploads/reminders/police.pdf",
    )
    assert reminder.category_emoji == '🎂'
    assert "24 Ekim" in reminder.target_date_display

    data = reminder.to_dict()
    assert data['title'] == "Eşimin Doğum Günü"
    assert data['category'] == "Doğum Günü"
    assert data['amount'] == 500.0
    assert data['document_url'] == "/static/uploads/reminders/police.pdf"


@pytest.mark.unit
def test_reminder_application_service_orchestration():
    """Test ReminderApplicationService methods with mocked repository."""
    mock_repo = MagicMock(spec=ReminderRepository)
    mock_domain = ReminderService()
    app_svc = ReminderApplicationService(
        reminder_repository=mock_repo,
        reminder_domain_service=mock_domain,
    )

    # 1. Create with invalid data should raise ValueError
    with pytest.raises(ValueError, match="Hatırlatıcı başlığı"):
        app_svc.create_reminder(
            tenant_id="t1",
            user_id=1,
            title="",
            frequency="Aylık",
            due_day=5,
        )

    # 2. Create with valid data and document_url
    mock_repo.create_reminder.return_value = MagicMock(id=1, title="Kira", document_url="/static/uploads/reminders/kira.pdf")
    result = app_svc.create_reminder(
        tenant_id="t1",
        user_id=1,
        title="Kira",
        category="Ödeme",
        frequency="Aylık",
        due_day=1,
        amount="15000",
        document_url="/static/uploads/reminders/kira.pdf",
    )
    assert result.id == 1
    assert result.document_url == "/static/uploads/reminders/kira.pdf"
    mock_repo.create_reminder.assert_called_once()


@pytest.mark.unit
def test_reminder_vehicle_maintenance_category_emoji():
    """Verify vehicle maintenance categories return car emoji."""
    reminder = UserReminder(
        tenant_id="tenant_1",
        title="TÜVTÜRK Araç Muayenesi",
        category="Araç & Bakım",
        frequency="Tek Seferlik",
        due_date="2027-04-15",
    )
    assert reminder.category_emoji == '🚗'
