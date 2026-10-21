"""
End-to-End Combinations and Edge-Case Tests for Recurring Plans.
Validates all flows, frequencies, duration modes, date synchronizations,
leap-year & month-end clamps, and bidirectional calculations.
"""

from datetime import date, datetime
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from domain.planning.services.plan_service import PlanService
from validators.request_validators import (
    _calc_end_date,
    _calc_installments,
    plan_form_from_request,
)


@pytest.mark.unit
class TestPlanCombinationsMatrix:
    """Test every combination of Flow, Frequency, and Duration Mode."""

    @pytest.mark.parametrize("flow_action, flow_type", [
        ("add_expense_plan", "Abonelik"),
        ("add_income_plan", "Abonelik"),
        ("add_investment_plan", "DCA"),
    ])
    def test_indefinite_plans_all_flows(self, flow_action, flow_type):
        """Indefinite plans for Expense, Income, and Investment DCA."""
        form = {
            'action': flow_action,
            'name': f'Test {flow_action}',
            'category': 'Genel',
            'amount': '1500.00',
            'installments': '0',
            'payment_day': '15',
            'start_date': '2026-11-15',
            'plan_type': flow_type,
            'frequency': 'Aylık',
            'target_asset_id': '10' if 'investment' in flow_action else '',
        }
        dto = plan_form_from_request(form)
        assert dto.amount == Decimal('1500.00')
        assert dto.payment_day == 15
        assert dto.start_date == '2026-11-15'
        assert dto.installments == 0
        assert dto.end_date is None
        assert dto.plan_type == flow_type
        if 'investment' in flow_action:
            assert dto.target_asset_id == 10

    @pytest.mark.parametrize("frequency, installments, expected_end", [
        ("Aylık", 12, date(2027, 10, 15)),
        ("Aylık", 6, date(2027, 4, 15)),
        ("Haftalık", 4, date(2026, 12, 6)),
        ("3-Aylık", 4, date(2027, 8, 15)),
        ("Yıllık", 3, date(2028, 11, 15)),
    ])
    def test_installment_auto_derives_end_date_all_frequencies(self, frequency, installments, expected_end):
        """Form with installments only auto-derives exact end_date for all frequencies."""
        form = {
            'action': 'add_expense_plan',
            'name': f'Taksit {frequency}',
            'category': 'Kredi',
            'amount': '2500',
            'installments': str(installments),
            'payment_day': '15',
            'start_date': '2026-11-15',
            'plan_type': 'Taksit',
            'frequency': frequency,
            'end_date': '',
        }
        dto = plan_form_from_request(form)
        assert dto.installments == installments
        assert dto.end_date == expected_end.strftime('%Y-%m-%d')

    @pytest.mark.parametrize("frequency, end_date_str, expected_installments", [
        ("Aylık", "2027-10-15", 12),
        ("Aylık", "2027-04-15", 6),
        ("Haftalık", "2026-12-06", 4),
        ("3-Aylık", "2027-08-15", 4),
        ("Yıllık", "2028-11-15", 3),
    ])
    def test_end_date_auto_derives_installments_all_frequencies(self, frequency, end_date_str, expected_installments):
        """Form with end_date only auto-derives exact installments count for all frequencies."""
        form = {
            'action': 'add_expense_plan',
            'name': f'Bitiş {frequency}',
            'category': 'Kredi',
            'amount': '2500',
            'installments': '0',
            'payment_day': '15',
            'start_date': '2026-11-15',
            'plan_type': 'Taksit',
            'frequency': frequency,
            'end_date': end_date_str,
        }
        dto = plan_form_from_request(form)
        assert dto.installments == expected_installments
        assert dto.end_date == end_date_str


@pytest.mark.unit
class TestPlanDateEdgeCasesAndClamping:
    """Test date boundaries, leap years, month-ends and clampings."""

    def test_payment_day_clamped_to_february_28_in_non_leap_year(self):
        """Payment day 31 in February 2026 clamps to 28."""
        form = {
            'action': 'add_expense_plan',
            'name': 'Feb clamp',
            'category': 'Aidat',
            'amount': '500',
            'payment_day': '31',
            'start_date': '2026-02-15',
        }
        dto = plan_form_from_request(form)
        assert dto.payment_day == 28

    def test_payment_day_clamped_to_february_29_in_leap_year(self):
        """Payment day 31 in February 2028 (leap year) clamps to 29."""
        form = {
            'action': 'add_expense_plan',
            'name': 'Feb leap clamp',
            'category': 'Aidat',
            'amount': '500',
            'payment_day': '31',
            'start_date': '2028-02-15',
        }
        dto = plan_form_from_request(form)
        assert dto.payment_day == 29

    def test_payment_day_clamped_to_30_in_april(self):
        """Payment day 31 in April clamps to 30."""
        form = {
            'action': 'add_expense_plan',
            'name': 'April clamp',
            'category': 'Aidat',
            'amount': '500',
            'payment_day': '31',
            'start_date': '2026-04-10',
        }
        dto = plan_form_from_request(form)
        assert dto.payment_day == 30

    def test_start_date_day_overflow_sanitized(self):
        """Invalid date 2026-02-30 is sanitized cleanly to 2026-02-28 without 500 error."""
        form = {
            'action': 'add_expense_plan',
            'name': 'Overflow test',
            'category': 'Aidat',
            'amount': '500',
            'payment_day': '28',
            'start_date': '2026-02-30',
        }
        dto = plan_form_from_request(form)
        assert dto.start_date == '2026-02-28'

    def test_calc_end_date_january_31_plus_one_month_clamps_to_february(self):
        """_calc_end_date from Jan 31 + 2 installments gives Feb 28 in non-leap year."""
        end = _calc_end_date(date(2026, 1, 31), 2, "Aylık")
        assert end == date(2026, 2, 28)

    def test_calc_end_date_january_31_plus_one_month_clamps_to_february_leap_year(self):
        """_calc_end_date from Jan 31 2028 + 2 installments gives Feb 29 in leap year."""
        end = _calc_end_date(date(2028, 1, 31), 2, "Aylık")
        assert end == date(2028, 2, 29)

    def test_calc_end_date_august_31_quarterly_clamps_to_november_30(self):
        """_calc_end_date from Aug 31 + 2 quarters (3 months) gives Nov 30."""
        end = _calc_end_date(date(2026, 8, 31), 2, "3-Aylık")
        assert end == date(2026, 11, 30)


@pytest.mark.unit
class TestPlanEditActionTransitions:
    """Test lifecycle shifts, start_date modifications and edit mode behaviors."""

    def test_edit_plan_shifting_start_date_past_old_end_date_shifts_end_date(self):
        """Editing plan and setting start_date after previous end_date preserves installment count and extends end_date."""
        form = {
            'action': 'update_plan',
            'plan_id': '42',
            'name': 'Shifted plan',
            'category': 'Kredi',
            'amount': '1000',
            'installments': '6',
            'payment_day': '15',
            'start_date': '2028-01-15',  # Far past old end date 2026-06-15
            'end_date': '2026-06-15',
            'plan_type': 'Taksit',
            'frequency': 'Aylık',
        }
        dto = plan_form_from_request(form)
        assert dto.start_date == '2028-01-15'
        assert dto.installments == 6
        assert dto.end_date == '2028-06-15'

    def test_plan_service_save_plan_full_lifecycle(self, app):
        """PlanService properly orchestrates repository and occurrence schedule sync."""
        from flask import g

        financial_repo = Mock()
        catalog_repo = Mock()
        occurrence_service = Mock()

        created_plan = SimpleNamespace(id=99, tenant_id="tenant-123")
        financial_repo.add_recurring_plan.return_value = created_plan

        form = {
            'action': 'add_expense_plan',
            'name': 'Yeni Cihaz Taksiti',
            'category': 'Teknoloji',
            'amount': '3500.00',
            'installments': '12',
            'payment_day': '20',
            'start_date': '2026-11-20',
            'plan_type': 'Taksit',
            'frequency': 'Aylık',
            'end_date': '2027-10-20',
        }
        dto = plan_form_from_request(form)

        with app.app_context():
            g.tenant_id = "tenant-123"
            service = PlanService(financial_repo, catalog_repo, occurrence_service)
            msg = service.save_plan(dto)

        assert "başarıyla eklendi" in msg
        financial_repo.add_recurring_plan.assert_called_once()
        occurrence_service.sync_plan.assert_called_once_with(created_plan, "tenant-123")
