"""
Unit Tests - Notification Rules
Tests for notification rule evaluation logic
"""

from datetime import datetime
from unittest.mock import Mock, patch

import pytest

from domain.notifications.services.notification_rules import (
    BUDGET_WARN_RATIO,
    _month_bounds,
    evaluate_all,
    evaluate_budget_alerts,
    evaluate_payment_alerts,
)


@pytest.mark.unit
class TestNotificationRules:
    """Test notification rule evaluation"""

    def test_budget_warn_ratio_constant(self):
        """Test BUDGET_WARN_RATIO constant"""
        assert float(BUDGET_WARN_RATIO) == 0.80

    def test_month_bounds(self):
        """Test _month_bounds function"""
        today = datetime(2026, 8, 15)
        start, end = _month_bounds(today)

        assert start == '2026-08-01'
        assert end == '2026-08-15'

    def test_month_bounds_first_day(self):
        """Test _month_bounds on first day of month"""
        today = datetime(2026, 8, 1)
        start, end = _month_bounds(today)

        assert start == '2026-08-01'
        assert end == '2026-08-01'

    def test_evaluate_budget_alerts_no_categories(self):
        """Test evaluate_budget_alerts with no categories"""
        with patch('domain.catalog.models.catalog_models.Category') as mock_category:
            mock_category.query.filter.return_value.all.return_value = []

            result = evaluate_budget_alerts(tenant_id='test_tenant')

            assert result == []

    def test_evaluate_budget_alerts_zero_limit(self):
        """Test evaluate_budget_alerts with zero budget limit"""
        with patch('domain.catalog.models.catalog_models.Category') as mock_category:
            mock_cat = Mock()
            mock_cat.budget_limit = 0
            mock_cat.name = 'Test'
            mock_cat.id = 1
            mock_category.query.filter.return_value.all.return_value = [mock_cat]

            result = evaluate_budget_alerts(tenant_id='test_tenant')

            assert result == []

    def test_evaluate_budget_alerts_under_threshold(self, app):
        """No alert is emitted below the 80% budget threshold."""
        from domain.catalog.models.catalog_models import Category
        from models import Transaction, db

        with app.app_context():
            category = Category(name='Budget Under', type='Gider', budget_limit=1000, tenant_id='default')
            db.session.add(category)
            db.session.add(Transaction(
                date='2026-08-10', category='Budget Under', type='Gider',
                status='Ödendi', amount=500, tenant_id='default'
            ))
            db.session.commit()
            result = evaluate_budget_alerts('default', today=datetime(2026, 8, 15))

        assert result == []

    def test_evaluate_budget_alerts_warning_level(self, app):
        """An 80% budget usage emits a warning draft."""
        from domain.catalog.models.catalog_models import Category
        from models import Transaction, db

        with app.app_context():
            category = Category(name='Budget Warning', type='Gider', budget_limit=1000, tenant_id='default')
            db.session.add(category)
            db.session.add(Transaction(
                date='2026-08-10', category='Budget Warning', type='Gider',
                status='Ödendi', amount=800, tenant_id='default'
            ))
            db.session.commit()
            result = evaluate_budget_alerts('default', today=datetime(2026, 8, 15))

        assert len(result) == 1
        assert result[0]['severity'] == 'warning'
        assert result[0]['category'] == 'budget'

    def test_evaluate_budget_alerts_danger_level(self, app):
        """A budget breach emits a danger draft."""
        from domain.catalog.models.catalog_models import Category
        from models import Transaction, db

        with app.app_context():
            category = Category(name='Budget Danger', type='Gider', budget_limit=1000, tenant_id='default')
            db.session.add(category)
            db.session.add(Transaction(
                date='2026-08-10', category='Budget Danger', type='Gider',
                status='Ödendi', amount=1200, tenant_id='default'
            ))
            db.session.commit()
            result = evaluate_budget_alerts('default', today=datetime(2026, 8, 15))

        assert len(result) == 1
        assert result[0]['severity'] == 'danger'
        assert 'aşıldı' in result[0]['title']

    def test_evaluate_payment_alerts_no_pending(self, app):
        """No pending payment produces no payment draft."""
        with app.app_context():
            assert evaluate_payment_alerts(
                'default', today=datetime(2026, 8, 15)
            ) == []

    def test_evaluate_payment_alerts_overdue(self, app):
        """An overdue pending expense emits a danger draft."""
        from models import Transaction, db

        with app.app_context():
            db.session.add(Transaction(
                date='2026-08-14', category='Kredi', description='Gecikmiş kredi',
                type='Gider', status='Bekliyor', amount=300, tenant_id='default'
            ))
            db.session.commit()
            result = evaluate_payment_alerts('default', today=datetime(2026, 8, 15))

        assert len(result) == 1
        assert result[0]['severity'] == 'danger'
        assert 'Gecikmiş kredi' in result[0]['title']

    def test_evaluate_payment_alerts_upcoming(self, app):
        """An upcoming pending expense within the horizon emits a warning draft."""
        from models import Transaction, db

        with app.app_context():
            db.session.add(Transaction(
                date='2026-08-17', category='Fatura', description='Yaklaşan fatura',
                type='Gider', status='Bekliyor', amount=150, tenant_id='default'
            ))
            db.session.commit()
            result = evaluate_payment_alerts('default', reminder_days=3, today=datetime(2026, 8, 15))

        assert len(result) == 1
        assert result[0]['severity'] == 'warning'
        assert 'Yaklaşan fatura' in result[0]['title']

    def test_evaluate_payment_alerts_custom_reminder_days(self, app):
        """Custom reminder days extend the upcoming-payment horizon."""
        from models import Transaction, db

        with app.app_context():
            db.session.add(Transaction(
                date='2026-08-20', category='Fatura', description='Beş günlük fatura',
                type='Gider', status='Bekliyor', amount=150, tenant_id='default'
            ))
            db.session.commit()
            result = evaluate_payment_alerts('default', reminder_days=5, today=datetime(2026, 8, 15))

        assert len(result) == 1
        assert result[0]['severity'] == 'warning'

    @patch('domain.notifications.services.notification_rules.evaluate_asset_alerts', return_value=[])
    @patch('domain.notifications.services.notification_rules.evaluate_portfolio_alerts', return_value=[])
    @patch('domain.notifications.services.notification_rules.evaluate_macro_ratio_alerts', return_value=[])
    def test_evaluate_all_default_preferences(self, *mocks):
        """Test evaluate_all with default preferences"""
        with patch('domain.notifications.services.notification_rules.evaluate_budget_alerts') as mock_budget, \
             patch('domain.notifications.services.notification_rules.evaluate_payment_alerts') as mock_payment:
            mock_budget.return_value = [{'category': 'budget'}]
            mock_payment.return_value = [{'category': 'payment'}]

            result = evaluate_all(tenant_id='test_tenant')

            assert len(result) == 2
            mock_budget.assert_called_once()
            mock_payment.assert_called_once()

    @patch('domain.notifications.services.notification_rules.evaluate_asset_alerts', return_value=[])
    @patch('domain.notifications.services.notification_rules.evaluate_portfolio_alerts', return_value=[])
    @patch('domain.notifications.services.notification_rules.evaluate_macro_ratio_alerts', return_value=[])
    def test_evaluate_all_custom_preferences(self, *mocks):
        """Test evaluate_all with custom preferences"""
        mock_preferences = Mock()
        mock_preferences.notify_budget = False
        mock_preferences.notify_payments = True
        mock_preferences.payment_reminder_days = 5

        with patch('domain.notifications.services.notification_rules.evaluate_budget_alerts') as mock_budget, \
             patch('domain.notifications.services.notification_rules.evaluate_payment_alerts') as mock_payment:
            mock_budget.return_value = []
            mock_payment.return_value = [{'category': 'payment'}]

            result = evaluate_all(tenant_id='test_tenant', preferences=mock_preferences)

            assert len(result) == 1
            mock_budget.assert_not_called()
            mock_payment.assert_called_once()

    @patch('domain.notifications.services.notification_rules.evaluate_asset_alerts', return_value=[])
    @patch('domain.notifications.services.notification_rules.evaluate_portfolio_alerts', return_value=[])
    @patch('domain.notifications.services.notification_rules.evaluate_macro_ratio_alerts', return_value=[])
    def test_evaluate_all_with_preferences(self, *mocks):
        """Test evaluate_all with user preferences"""
        mock_preferences = Mock()
        mock_preferences.notify_budget = True
        mock_preferences.notify_payments = False
        mock_preferences.payment_reminder_days = 5

        with patch('domain.notifications.services.notification_rules.evaluate_budget_alerts') as mock_budget, \
             patch('domain.notifications.services.notification_rules.evaluate_payment_alerts') as mock_payment:

            mock_budget.return_value = ['draft1']

            drafts = evaluate_all(tenant_id='test_tenant', preferences=mock_preferences)

            assert len(drafts) == 1
            mock_budget.assert_called_once()
            mock_payment.assert_not_called()

    @patch('domain.notifications.services.notification_rules.evaluate_asset_alerts', return_value=[])
    @patch('domain.notifications.services.notification_rules.evaluate_portfolio_alerts', return_value=[])
    @patch('domain.notifications.services.notification_rules.evaluate_macro_ratio_alerts', return_value=[])
    def test_evaluate_all_budget_disabled(self, *mocks):
        """Test evaluate_all with budget notifications disabled"""
        mock_preferences = Mock()
        mock_preferences.notify_budget = False
        mock_preferences.notify_payments = True

        with patch('domain.notifications.services.notification_rules.evaluate_budget_alerts') as mock_budget, \
             patch('domain.notifications.services.notification_rules.evaluate_payment_alerts') as mock_payment:
            mock_budget.return_value = []
            mock_payment.return_value = [{'category': 'payment'}]

            result = evaluate_all(tenant_id='test_tenant', preferences=mock_preferences)

            assert len(result) == 1
            mock_budget.assert_not_called()
            mock_payment.assert_called_once()

    def test_evaluate_payment_alerts_custom_reminder_days_duplicate(self, app):
        """The duplicate custom-reminder path follows the same horizon contract."""
        from models import Transaction, db

        with app.app_context():
            db.session.add(Transaction(
                date='2026-08-20', category='Fatura', description='Tekrarsız fatura',
                type='Gider', status='Bekliyor', amount=150, tenant_id='default'
            ))
            db.session.commit()
            result = evaluate_payment_alerts('default', reminder_days=5, today=datetime(2026, 8, 15))

        assert [draft['dedupe_key'] for draft in result] == [f'payment:{result[0]["dedupe_key"].split(":")[1]}:due']
