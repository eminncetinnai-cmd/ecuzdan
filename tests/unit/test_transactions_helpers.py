"""
Unit Tests - Transaction Route Pure Helpers
Flask context gerektirmeyen saf yardımcı fonksiyonlar.
  - _transaction_ui_options()
  - _serialize_transaction()
  - _serialize_occurrence()
  - _serialize_payment()
  - _serialize_adjustment()
  - _serialize_audit_event()
"""

from datetime import date, datetime
from decimal import Decimal
from unittest.mock import MagicMock

import pytest

from routes.transactions import (
    _TRANSACTION_STATUS_OPTIONS,
    _TRANSACTION_TYPE_OPTIONS,
    _serialize_adjustment,
    _serialize_audit_event,
    _serialize_occurrence,
    _serialize_payment,
    _serialize_transaction,
    _transaction_ui_options,
)

# ── _transaction_ui_options() ──────────────────────────────────────────────────

class TestTransactionUIOptions:
    @pytest.mark.unit
    def test_returns_dict_with_expected_keys(self):
        """Dönen dict beklenen tüm anahtarları içermeli."""
        opts = _transaction_ui_options()
        assert 'type_options' in opts
        assert 'status_options' in opts
        assert 'type_values' in opts
        assert 'status_values' in opts
        assert 'type_label_keys' in opts
        assert 'status_label_keys' in opts

    @pytest.mark.unit
    def test_type_options_count(self):
        """type_options 4 giriş içermeli (Gelir/Gider/Yatırım/Transfer)."""
        opts = _transaction_ui_options()
        assert len(opts['type_options']) == 4

    @pytest.mark.unit
    def test_status_options_count(self):
        """status_options 2 giriş içermeli (Ödendi/Bekliyor)."""
        opts = _transaction_ui_options()
        assert len(opts['status_options']) == 2

    @pytest.mark.unit
    def test_type_options_structure(self):
        """Her type_option dom_key, value ve label_key içermeli."""
        opts = _transaction_ui_options()
        for item in opts['type_options']:
            assert 'dom_key' in item
            assert 'value' in item
            assert 'label_key' in item

    @pytest.mark.unit
    def test_status_options_structure(self):
        """Her status_option dom_key, value ve label_key içermeli."""
        opts = _transaction_ui_options()
        for item in opts['status_options']:
            assert 'dom_key' in item
            assert 'value' in item
            assert 'label_key' in item

    @pytest.mark.unit
    def test_type_values_has_four_keys(self):
        """type_values income/expense/investment/transfer içermeli."""
        opts = _transaction_ui_options()
        tv = opts['type_values']
        assert 'income' in tv
        assert 'expense' in tv
        assert 'investment' in tv
        assert 'transfer' in tv

    @pytest.mark.unit
    def test_status_values_has_two_keys(self):
        """status_values paid/pending içermeli."""
        opts = _transaction_ui_options()
        sv = opts['status_values']
        assert 'paid' in sv
        assert 'pending' in sv

    @pytest.mark.unit
    def test_type_label_keys_maps_each_type_value(self):
        """type_label_keys her tip değerini bir label_key'e eşlemeli."""
        opts = _transaction_ui_options()
        for _, value, _ in _TRANSACTION_TYPE_OPTIONS:
            assert value in opts['type_label_keys']

    @pytest.mark.unit
    def test_status_label_keys_maps_each_status_value(self):
        """status_label_keys her durum değerini bir label_key'e eşlemeli."""
        opts = _transaction_ui_options()
        for _, value, _ in _TRANSACTION_STATUS_OPTIONS:
            assert value in opts['status_label_keys']

    @pytest.mark.unit
    def test_result_is_stable_across_calls(self):
        """Birden fazla çağrı tutarlı sonuç dönmeli."""
        opts1 = _transaction_ui_options()
        opts2 = _transaction_ui_options()
        assert opts1['type_values'] == opts2['type_values']
        assert opts1['status_values'] == opts2['status_values']


# ── _serialize_transaction() ───────────────────────────────────────────────────

def _make_transaction(**kwargs):
    """Test için minimal sahte Transaction nesnesi."""
    tx = MagicMock()
    tx.id = kwargs.get('id', 1)
    tx.tenant_id = kwargs.get('tenant_id', 10)
    tx.date = kwargs.get('date', date(2025, 1, 15))
    tx.category = kwargs.get('category', 'Gıda')
    tx.description = kwargs.get('description', 'Market')
    tx.note = kwargs.get('note', 'Test notu')
    tx.type = kwargs.get('type', 'Gider')
    tx.status = kwargs.get('status', 'Ödendi')
    tx.amount = kwargs.get('amount', Decimal('150.00'))
    tx.source_type = kwargs.get('source_type', 'manual')
    tx.source_id = kwargs.get('source_id', None)
    tx.bank_account_id = kwargs.get('bank_account_id', None)
    tx.installment_number = kwargs.get('installment_number', None)
    tx.version = kwargs.get('version', 1)
    tx.is_deleted = kwargs.get('is_deleted', False)
    return tx


class TestSerializeTransaction:
    @pytest.mark.unit
    def test_basic_fields_serialized(self):
        """Temel alanlar doğru serileştirilmeli."""
        tx = _make_transaction()
        result = _serialize_transaction(tx)
        assert result['id'] == 1
        assert result['tenant_id'] == 10
        assert result['category'] == 'Gıda'
        assert result['description'] == 'Market'
        assert result['type'] == 'Gider'
        assert result['status'] == 'Ödendi'

    @pytest.mark.unit
    def test_amount_serialized_as_string(self):
        """amount string olarak serileştirilmeli."""
        tx = _make_transaction(amount=Decimal('1234.56'))
        result = _serialize_transaction(tx)
        assert result['amount'] == '1234.56'

    @pytest.mark.unit
    def test_amount_none_becomes_zero_string(self):
        """amount=None olduğunda '0' döndürülmeli."""
        tx = _make_transaction(amount=None)
        result = _serialize_transaction(tx)
        assert result['amount'] == '0'

    @pytest.mark.unit
    def test_is_deleted_as_bool(self):
        """is_deleted bool olarak serileştirilmeli."""
        tx = _make_transaction(is_deleted=True)
        result = _serialize_transaction(tx)
        assert result['is_deleted'] is True

    @pytest.mark.unit
    def test_source_type_captured(self):
        """source_type doğru aktarılmalı."""
        tx = _make_transaction(source_type='plan')
        result = _serialize_transaction(tx)
        assert result['source_type'] == 'plan'

    @pytest.mark.unit
    def test_version_captured(self):
        """version doğru aktarılmalı."""
        tx = _make_transaction(version=5)
        result = _serialize_transaction(tx)
        assert result['version'] == 5


# ── _serialize_occurrence() ────────────────────────────────────────────────────

def _make_occurrence(**kwargs):
    occ = MagicMock()
    occ.id = kwargs.get('id', 1)
    occ.plan_id = kwargs.get('plan_id', 2)
    occ.tenant_id = kwargs.get('tenant_id', 10)
    occ.occurrence_number = kwargs.get('occurrence_number', 1)
    occ.scheduled_date = kwargs.get('scheduled_date', date(2025, 2, 1))
    occ.status = kwargs.get('status', 'Bekliyor')
    occ.amount = kwargs.get('amount', Decimal('500.00'))
    occ.transaction_id = kwargs.get('transaction_id', None)
    occ.paid_at = kwargs.get('paid_at', None)
    occ.notes = kwargs.get('notes', None)
    return occ


class TestSerializeOccurrence:
    @pytest.mark.unit
    def test_basic_fields(self):
        occ = _make_occurrence()
        result = _serialize_occurrence(occ)
        assert result['id'] == 1
        assert result['plan_id'] == 2
        assert result['tenant_id'] == 10
        assert result['status'] == 'Bekliyor'

    @pytest.mark.unit
    def test_amount_as_string(self):
        occ = _make_occurrence(amount=Decimal('250.00'))
        result = _serialize_occurrence(occ)
        assert result['amount'] == '250.00'

    @pytest.mark.unit
    def test_amount_none_becomes_none(self):
        occ = _make_occurrence(amount=None)
        result = _serialize_occurrence(occ)
        assert result['amount'] is None

    @pytest.mark.unit
    def test_paid_at_none(self):
        occ = _make_occurrence(paid_at=None)
        result = _serialize_occurrence(occ)
        assert result['paid_at'] is None

    @pytest.mark.unit
    def test_paid_at_isoformat(self):
        dt = datetime(2025, 3, 10, 12, 0, 0)
        occ = _make_occurrence(paid_at=dt)
        result = _serialize_occurrence(occ)
        assert result['paid_at'] == dt.isoformat()


# ── _serialize_payment() ───────────────────────────────────────────────────────

def _make_payment(**kwargs):
    p = MagicMock()
    p.id = kwargs.get('id', 1)
    p.plan_id = kwargs.get('plan_id', 3)
    p.tenant_id = kwargs.get('tenant_id', 10)
    p.amount = kwargs.get('amount', Decimal('300.00'))
    p.payment_date = kwargs.get('payment_date', date(2025, 4, 1))
    p.installment_number = kwargs.get('installment_number', 1)
    p.transaction_id = kwargs.get('transaction_id', 42)
    p.notes = kwargs.get('notes', 'Ödeme notu')
    return p


class TestSerializePayment:
    @pytest.mark.unit
    def test_basic_fields(self):
        p = _make_payment()
        result = _serialize_payment(p)
        assert result['id'] == 1
        assert result['plan_id'] == 3
        assert result['tenant_id'] == 10
        assert result['installment_number'] == 1

    @pytest.mark.unit
    def test_amount_as_string(self):
        p = _make_payment(amount=Decimal('750.50'))
        result = _serialize_payment(p)
        assert result['amount'] == '750.50'

    @pytest.mark.unit
    def test_transaction_id_captured(self):
        p = _make_payment(transaction_id=99)
        result = _serialize_payment(p)
        assert result['transaction_id'] == 99

    @pytest.mark.unit
    def test_notes_captured(self):
        p = _make_payment(notes='Son taksit')
        result = _serialize_payment(p)
        assert result['notes'] == 'Son taksit'


# ── _serialize_adjustment() ────────────────────────────────────────────────────

def _make_adjustment(**kwargs):
    adj = MagicMock()
    adj.id = kwargs.get('id', 1)
    adj.tenant_id = kwargs.get('tenant_id', 10)
    adj.original_transaction_id = kwargs.get('original_transaction_id', 5)
    adj.compensating_transaction_id = kwargs.get('compensating_transaction_id', None)
    adj.kind = kwargs.get('kind', 'adjustment')
    adj.status = kwargs.get('status', 'applied')
    adj.amount_delta = kwargs.get('amount_delta', Decimal('50.00'))
    adj.original_amount_snapshot = kwargs.get('original_amount_snapshot', Decimal('200.00'))
    adj.original_type_snapshot = kwargs.get('original_type_snapshot', 'Gider')
    adj.original_category_snapshot = kwargs.get('original_category_snapshot', 'Gıda')
    adj.original_date_snapshot = kwargs.get('original_date_snapshot', date(2025, 1, 1))
    adj.original_version = kwargs.get('original_version', 1)
    adj.reason_code = kwargs.get('reason_code', 'other')
    adj.reason_text = kwargs.get('reason_text', 'Düzeltme')
    adj.requested_by = kwargs.get('requested_by', 1)
    adj.approved_by = kwargs.get('approved_by', None)
    adj.requested_at = kwargs.get('requested_at', None)
    adj.applied_at = kwargs.get('applied_at', None)
    adj.failure_code = kwargs.get('failure_code', None)
    adj.failure_message = kwargs.get('failure_message', None)
    adj.idempotency_key = kwargs.get('idempotency_key', 'key-xyz')
    adj.correlation_id = kwargs.get('correlation_id', 'corr-123')
    adj.metadata_json = kwargs.get('metadata_json', {})
    return adj


class TestSerializeAdjustment:
    @pytest.mark.unit
    def test_basic_fields(self):
        adj = _make_adjustment()
        result = _serialize_adjustment(adj)
        assert result['id'] == 1
        assert result['tenant_id'] == 10
        assert result['kind'] == 'adjustment'
        assert result['status'] == 'applied'

    @pytest.mark.unit
    def test_amounts_as_string(self):
        adj = _make_adjustment(
            amount_delta=Decimal('25.00'),
            original_amount_snapshot=Decimal('100.00')
        )
        result = _serialize_adjustment(adj)
        assert result['amount_delta'] == '25.00'
        assert result['original_amount_snapshot'] == '100.00'

    @pytest.mark.unit
    def test_requested_at_none(self):
        adj = _make_adjustment(requested_at=None)
        result = _serialize_adjustment(adj)
        assert result['requested_at'] is None

    @pytest.mark.unit
    def test_requested_at_isoformat(self):
        dt = datetime(2025, 5, 20, 10, 30, 0)
        adj = _make_adjustment(requested_at=dt)
        result = _serialize_adjustment(adj)
        assert result['requested_at'] == dt.isoformat()

    @pytest.mark.unit
    def test_applied_at_isoformat(self):
        dt = datetime(2025, 5, 21, 9, 0, 0)
        adj = _make_adjustment(applied_at=dt)
        result = _serialize_adjustment(adj)
        assert result['applied_at'] == dt.isoformat()

    @pytest.mark.unit
    def test_idempotency_key_captured(self):
        adj = _make_adjustment(idempotency_key='unique-key-123')
        result = _serialize_adjustment(adj)
        assert result['idempotency_key'] == 'unique-key-123'


# ── _serialize_audit_event() ───────────────────────────────────────────────────

def _make_audit_event(**kwargs):
    ev = MagicMock()
    ev.id = kwargs.get('id', 1)
    ev.tenant_id = kwargs.get('tenant_id', 10)
    ev.adjustment_id = kwargs.get('adjustment_id', 1)
    ev.transaction_id = kwargs.get('transaction_id', 5)
    ev.event_type = kwargs.get('event_type', 'adjustment_applied')
    ev.actor_user_id = kwargs.get('actor_user_id', 1)
    ev.correlation_id = kwargs.get('correlation_id', 'corr-abc')
    ev.request_id = kwargs.get('request_id', 'req-xyz')
    ev.occurred_at = kwargs.get('occurred_at', None)
    ev.previous_hash = kwargs.get('previous_hash', 'prevhash')
    ev.event_hash = kwargs.get('event_hash', 'eventhash')
    ev.payload = kwargs.get('payload', {'key': 'value'})
    return ev


class TestSerializeAuditEvent:
    @pytest.mark.unit
    def test_basic_fields(self):
        ev = _make_audit_event()
        result = _serialize_audit_event(ev)
        assert result['id'] == 1
        assert result['event_type'] == 'adjustment_applied'
        assert result['actor_user_id'] == 1
        assert result['correlation_id'] == 'corr-abc'

    @pytest.mark.unit
    def test_occurred_at_none(self):
        ev = _make_audit_event(occurred_at=None)
        result = _serialize_audit_event(ev)
        assert result['occurred_at'] is None

    @pytest.mark.unit
    def test_occurred_at_isoformat(self):
        dt = datetime(2025, 6, 15, 8, 0, 0)
        ev = _make_audit_event(occurred_at=dt)
        result = _serialize_audit_event(ev)
        assert result['occurred_at'] == dt.isoformat()

    @pytest.mark.unit
    def test_hashes_captured(self):
        ev = _make_audit_event(previous_hash='p123', event_hash='e456')
        result = _serialize_audit_event(ev)
        assert result['previous_hash'] == 'p123'
        assert result['event_hash'] == 'e456'

    @pytest.mark.unit
    def test_payload_captured(self):
        payload = {'amount': '100', 'type': 'Gider'}
        ev = _make_audit_event(payload=payload)
        result = _serialize_audit_event(ev)
        assert result['payload'] == payload
