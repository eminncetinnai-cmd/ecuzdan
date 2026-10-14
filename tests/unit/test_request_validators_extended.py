"""
Unit Tests - Request Validators (Extended)
Eksik dal kapsamını dolduran ek testler.
"""

from decimal import Decimal

import pytest

from validators.request_validators import (
    logbook_entry_from_request,
    payment_form_from_request,
    plan_form_from_request,
    transaction_form_from_request,
)

# ── transaction_form_from_request ─────────────────────────────────────────────

class TestTransactionFormBankAccount:
    @pytest.mark.unit
    def test_valid_bank_account_id(self):
        """bank_account_id rakamsal string ise int'e çevrilmeli."""
        form = {'amount': '150', 'bank_account_id': '7'}
        result = transaction_form_from_request(form)
        assert result.bank_account_id == 7

    @pytest.mark.unit
    def test_empty_bank_account_id_becomes_none(self):
        """Boş bank_account_id → None."""
        form = {'amount': '150', 'bank_account_id': ''}
        result = transaction_form_from_request(form)
        assert result.bank_account_id is None

    @pytest.mark.unit
    def test_none_bank_account_id_becomes_none(self):
        """bank_account_id hiç verilmemişse → None."""
        form = {'amount': '150'}
        result = transaction_form_from_request(form)
        assert result.bank_account_id is None

    @pytest.mark.unit
    def test_invalid_bank_account_id_raises(self):
        """Rakamsal olmayan bank_account_id ValueError fırlatmalı."""
        form = {'amount': '150', 'bank_account_id': 'abc'}
        with pytest.raises(ValueError, match="Banka hesabı kimliği geçersiz"):
            transaction_form_from_request(form)


class TestTransactionFormIdempotency:
    @pytest.mark.unit
    def test_idempotency_key_is_captured(self):
        """idempotency_key form'dan okunmalı."""
        form = {'amount': '100', 'idempotency_key': 'key-abc-123'}
        result = transaction_form_from_request(form)
        assert result.idempotency_key == 'key-abc-123'

    @pytest.mark.unit
    def test_empty_idempotency_key_becomes_none(self):
        """Boş idempotency_key → None."""
        form = {'amount': '100', 'idempotency_key': ''}
        result = transaction_form_from_request(form)
        assert result.idempotency_key is None

    @pytest.mark.unit
    def test_version_parsed_from_digit_string(self):
        """Rakamsal 'version' string'i int'e çevrilmeli."""
        form = {'amount': '100', 'version': '3'}
        result = transaction_form_from_request(form)
        assert result.version == 3

    @pytest.mark.unit
    def test_non_digit_version_becomes_none(self):
        """Rakam olmayan version → None."""
        form = {'amount': '100', 'version': 'abc'}
        result = transaction_form_from_request(form)
        assert result.version is None

    @pytest.mark.unit
    def test_missing_version_becomes_none(self):
        """version hiç verilmemişse → None."""
        form = {'amount': '100'}
        result = transaction_form_from_request(form)
        assert result.version is None


class TestTransactionFormDecimalPrecision:
    @pytest.mark.unit
    def test_amount_is_decimal(self):
        """amount Decimal tipinde dönmeli."""
        form = {'amount': '99.99'}
        result = transaction_form_from_request(form)
        assert isinstance(result.amount, Decimal)

    @pytest.mark.unit
    def test_large_amount(self):
        """Büyük tutar doğru işlenmeli."""
        form = {'amount': '9999999.99'}
        result = transaction_form_from_request(form)
        assert result.amount == Decimal('9999999.99')

    @pytest.mark.unit
    def test_whitespace_stripped_from_fields(self):
        """category, description, note alanlarından baştaki/sondaki boşluklar temizlenmeli."""
        form = {
            'amount': '50',
            'category': '  Gıda  ',
            'description': '  Market  ',
            'note': '  Haftalık alışveriş  ',
        }
        result = transaction_form_from_request(form)
        assert result.category == 'Gıda'
        assert result.description == 'Market'
        assert result.note == 'Haftalık alışveriş'


# ── plan_form_from_request ─────────────────────────────────────────────────────

class TestPlanFormDateValidation:
    @pytest.mark.unit
    def test_invalid_end_date_format_raises(self):
        """Geçersiz bitiş tarihi formatı ValueError fırlatmalı."""
        form = {
            'action': 'add_expense_plan',
            'amount': '1000',
            'installments': '12',
            'payment_day': '15',
            'start_date': '2025-01-01',
            'end_date': '31/12/2025',  # yanlış format
        }
        with pytest.raises(ValueError, match="Geçersiz bitiş tarihi formatı"):
            plan_form_from_request(form)

    @pytest.mark.unit
    def test_end_date_before_start_date_raises(self):
        """Bitiş tarihi başlangıç tarihinden önce olursa ValueError fırlatmalı."""
        form = {
            'action': 'add_expense_plan',
            'amount': '1000',
            'installments': '12',
            'payment_day': '15',
            'start_date': '2025-06-01',
            'end_date': '2025-01-01',
        }
        with pytest.raises(ValueError, match="Bitiş tarihi başlangıç tarihinden önce olamaz"):
            plan_form_from_request(form)

    @pytest.mark.unit
    def test_valid_start_and_end_dates_accepted(self):
        """Geçerli tarih çifti sorunsuz kabul edilmeli."""
        form = {
            'action': 'add_expense_plan',
            'amount': '1000',
            'installments': '12',
            'payment_day': '15',
            'start_date': '2025-01-01',
            'end_date': '2025-12-31',
        }
        result = plan_form_from_request(form)
        assert result.start_date == '2025-01-01'
        assert result.end_date == '2025-12-31'


class TestPlanFormPlanType:
    @pytest.mark.unit
    def test_invalid_plan_type_raises(self):
        """Desteklenmeyen plan_type ValueError fırlatmalı."""
        form = {
            'action': 'add_expense_plan',
            'amount': '1000',
            'installments': '12',
            'payment_day': '15',
            'plan_type': 'Geçersiz',
        }
        with pytest.raises(ValueError, match="Geçersiz plan tipi"):
            plan_form_from_request(form)

    @pytest.mark.unit
    def test_all_valid_plan_types_accepted(self):
        """Tüm geçerli plan tipleri kabul edilmeli."""
        base = {
            'action': 'add_expense_plan',
            'amount': '1000',
            'installments': '12',
            'payment_day': '15',
        }
        for ptype in ('Taksit', 'Abonelik', 'DCA', 'Dönemsel'):
            form = {**base, 'plan_type': ptype}
            result = plan_form_from_request(form)
            assert result.plan_type == ptype


class TestPlanFormFrequency:
    @pytest.mark.unit
    def test_invalid_frequency_raises(self):
        """Desteklenmeyen frequency ValueError fırlatmalı."""
        form = {
            'action': 'add_expense_plan',
            'amount': '1000',
            'installments': '12',
            'payment_day': '15',
            'frequency': 'Günlük',  # desteklenmiyor
        }
        with pytest.raises(ValueError, match="Geçersiz plan sıklığı"):
            plan_form_from_request(form)

    @pytest.mark.unit
    def test_all_valid_frequencies_accepted(self):
        """Tüm geçerli sıklıklar kabul edilmeli."""
        base = {
            'action': 'add_expense_plan',
            'amount': '1000',
            'installments': '12',
            'payment_day': '15',
        }
        for freq in ('Aylık', '3-Aylık', 'Yıllık', 'Haftalık'):
            form = {**base, 'frequency': freq}
            result = plan_form_from_request(form)
            assert result.frequency == freq


class TestPlanFormActions:
    @pytest.mark.unit
    def test_all_valid_actions_accepted(self):
        """Tüm geçerli aksiyonlar kabul edilmeli."""
        base = {
            'amount': '1000',
            'installments': '12',
            'payment_day': '15',
        }
        for action in ('add_income_plan', 'add_expense_plan', 'add_investment_plan'):
            form = {**base, 'action': action}
            result = plan_form_from_request(form)
            assert result.action == action

    @pytest.mark.unit
    def test_payment_day_boundary_1(self):
        """payment_day=1 geçerli olmalı."""
        form = {
            'action': 'add_expense_plan',
            'amount': '1000',
            'installments': '12',
            'payment_day': '1',
        }
        result = plan_form_from_request(form)
        assert result.payment_day == 1

    @pytest.mark.unit
    def test_payment_day_boundary_31(self):
        """payment_day=31 geçerli olmalı."""
        form = {
            'action': 'add_expense_plan',
            'amount': '1000',
            'installments': '12',
            'payment_day': '31',
        }
        result = plan_form_from_request(form)
        assert result.payment_day == 31

    @pytest.mark.unit
    def test_zero_installments_accepted_for_unlimited(self):
        """Süresiz planlar için taksit=0 kabul edilmeli."""
        form = {
            'action': 'add_expense_plan',
            'amount': '1000',
            'installments': '0',
            'payment_day': '15',
        }
        result = plan_form_from_request(form)
        assert result.installments == 0

    @pytest.mark.unit
    def test_version_parsed(self):
        """version rakamsal ise int'e çevrilmeli."""
        form = {
            'action': 'add_expense_plan',
            'amount': '1000',
            'installments': '12',
            'payment_day': '15',
            'version': '2',
        }
        result = plan_form_from_request(form)
        assert result.version == 2

    @pytest.mark.unit
    def test_version_non_digit_becomes_none(self):
        """version rakam değilse None olmalı."""
        form = {
            'action': 'add_expense_plan',
            'amount': '1000',
            'installments': '12',
            'payment_day': '15',
            'version': 'v2',
        }
        result = plan_form_from_request(form)
        assert result.version is None


# ── payment_form_from_request ──────────────────────────────────────────────────

class TestPaymentFormEdgeCases:
    @pytest.mark.unit
    def test_negative_amount_raises(self):
        """Negatif tutar ValueError fırlatmalı."""
        form = {
            'plan_id': '1',
            'amount': '-50',
            'payment_date': '2025-01-15',
        }
        with pytest.raises(ValueError, match="Geçerli bir ödeme tutarı girin"):
            payment_form_from_request(form)

    @pytest.mark.unit
    def test_notes_stripped_to_none_when_empty(self):
        """Boş notes → None."""
        form = {
            'plan_id': '1',
            'amount': '100',
            'payment_date': '2025-01-15',
            'notes': '   ',
        }
        result = payment_form_from_request(form)
        assert result.notes is None

    @pytest.mark.unit
    def test_notes_stripped_and_returned(self):
        """Boşluklu notes temizlenip döndürülmeli."""
        form = {
            'plan_id': '1',
            'amount': '100',
            'payment_date': '2025-01-15',
            'notes': '  İlk ödeme  ',
        }
        result = payment_form_from_request(form)
        assert result.notes == 'İlk ödeme'


# ── logbook_entry_from_request ─────────────────────────────────────────────────

class TestLogbookEntryEdgeCases:
    @pytest.mark.unit
    def test_whitespace_only_title_raises(self):
        """Sadece boşluktan oluşan başlık reddedilmeli."""
        form = {
            'title': '   ',
            'content': 'Test içerik',
            'entry_date': '2025-01-01',
        }
        with pytest.raises(ValueError, match="Başlık zorunludur"):
            logbook_entry_from_request(form)

    @pytest.mark.unit
    def test_whitespace_only_content_raises(self):
        """Sadece boşluktan oluşan içerik reddedilmeli."""
        form = {
            'title': 'Başlık',
            'content': '   ',
            'entry_date': '2025-01-01',
        }
        with pytest.raises(ValueError, match="İçerik zorunludur"):
            logbook_entry_from_request(form)

    @pytest.mark.unit
    def test_asset_id_and_transaction_id_captured(self):
        """asset_id ve transaction_id alanları okunmalı."""
        form = {
            'title': 'Test',
            'content': 'İçerik',
            'entry_date': '2025-01-01',
            'asset_id': '42',
            'transaction_id': '99',
        }
        result = logbook_entry_from_request(form)
        assert result.asset_id == '42'
        assert result.transaction_id == '99'

    @pytest.mark.unit
    def test_none_asset_id_becomes_none(self):
        """asset_id=None olduğunda None döndürülmeli."""
        form = {
            'title': 'Test',
            'content': 'İçerik',
            'entry_date': '2025-01-01',
            'asset_id': None,
        }
        result = logbook_entry_from_request(form)
        assert result.asset_id is None
