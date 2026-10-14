"""Unit tests for evaluate_macro_ratio_alerts in notification_rules."""

from unittest.mock import MagicMock, patch

from domain.notifications.services.notification_rules import (
    evaluate_all,
    evaluate_macro_ratio_alerts,
)


def test_evaluate_macro_ratio_alerts_structure():
    drafts = evaluate_macro_ratio_alerts(tenant_id=1)

    assert isinstance(drafts, list)
    # The default 20 ratios dataset has multiple elevated ratios (e.g. Buffett, CAPE)
    assert len(drafts) > 0

    for draft in drafts:
        assert draft['category'] == 'macro'
        assert draft['severity'] in ('danger', 'warning')
        assert 'dedupe_key' in draft
        assert draft['link'] in ('/global-ratios', '/central-bank-reserves')
        assert 'title' in draft
        assert 'body' in draft


@patch('domain.notifications.services.notification_rules.evaluate_budget_alerts', return_value=[])
@patch('domain.notifications.services.notification_rules.evaluate_payment_alerts', return_value=[])
@patch('domain.notifications.services.notification_rules.evaluate_asset_alerts', return_value=[])
@patch('domain.notifications.services.notification_rules.evaluate_portfolio_alerts', return_value=[])
def test_evaluate_all_includes_macro_alerts(*mocks):
    prefs = MagicMock()
    prefs.notify_budget = False
    prefs.notify_payments = False
    prefs.notify_assets = False
    prefs.notify_portfolio = False
    prefs.notify_macro = True
    prefs.payment_reminder_days = 3

    drafts = evaluate_all(tenant_id=1, preferences=prefs)
    macro_drafts = [d for d in drafts if d.get('category') == 'macro']
    assert len(macro_drafts) > 0


def test_evaluate_all_respects_notify_macro_false():
    prefs = MagicMock()
    prefs.notify_budget = False
    prefs.notify_payments = False
    prefs.notify_assets = False
    prefs.notify_portfolio = False
    prefs.notify_macro = False
    prefs.payment_reminder_days = 3

    drafts = evaluate_all(tenant_id=1, preferences=prefs)
    assert len(drafts) == 0
