"""
Unit Tests - Request Validators
Form DTO construction and validation functions
"""

import pytest
from validators.request_validators import (
    transaction_form_from_request,
    plan_form_from_request,
    payment_form_from_request,
    logbook_entry_from_request,
)


@pytest.mark.unit
def test_transaction_form_from_request_success():
    """Test transaction_form_from_request with valid data"""
    form = {
        'amount': '100.50',
        'category': 'Food',
        'description': 'Grocery shopping',
        'status': 'Ödendi',
        'date': '2025-01-01',
        'note': 'Weekly groceries',
    }
    
    result = transaction_form_from_request(form)
    assert result.amount == 100.50
    assert result.category == 'Food'
    assert result.description == 'Grocery shopping'
    assert result.status == 'Ödendi'
    assert result.date == '2025-01-01'
    assert result.note == 'Weekly groceries'


@pytest.mark.unit
def test_transaction_form_from_request_invalid_amount():
    """Test transaction_form_from_request with invalid amount"""
    form = {
        'amount': 'invalid',
        'category': 'Food',
        'description': 'Test',
    }
    
    with pytest.raises(ValueError, match="Geçersiz tutar değeri"):
        transaction_form_from_request(form)


@pytest.mark.unit
def test_transaction_form_from_request_zero_amount():
    """Test transaction_form_from_request with zero amount"""
    form = {
        'amount': '0',
        'category': 'Food',
        'description': 'Test',
    }
    
    with pytest.raises(ValueError, match="Tutar sıfırdan büyük olmalıdır"):
        transaction_form_from_request(form)


@pytest.mark.unit
def test_transaction_form_from_request_negative_amount():
    """Test transaction_form_from_request with negative amount"""
    form = {
        'amount': '-10',
        'category': 'Food',
        'description': 'Test',
    }
    
    with pytest.raises(ValueError, match="Tutar sıfırdan büyük olmalıdır"):
        transaction_form_from_request(form)


@pytest.mark.unit
def test_transaction_form_from_request_default_values():
    """Test transaction_form_from_request with default values"""
    form = {
        'amount': '50',
    }
    
    result = transaction_form_from_request(form)
    assert result.amount == 50
    assert result.category == ''
    assert result.description == ''
    assert result.status == 'Ödendi'
    assert result.date == ''
    assert result.note == ''


@pytest.mark.unit
def test_plan_form_from_request_success():
    """Test plan_form_from_request with valid data"""
    form = {
        'action': 'add_expense_plan',
        'name': 'Rent',
        'category': 'Housing',
        'amount': '1000',
        'installments': '12',
        'payment_day': '15',
        'note': 'Monthly rent',
        'plan_id': '1',
        'start_date': '2025-01-01',
        'plan_type': 'Taksit',
        'frequency': 'Aylık',
        'end_date': '2025-12-31',
        'target_asset_id': '5',
    }
    
    result = plan_form_from_request(form)
    assert result.action == 'add_expense_plan'
    assert result.name == 'Rent'
    assert result.category == 'Housing'
    assert result.amount == 1000
    assert result.installments == 12
    assert result.payment_day == 15
    assert result.note == 'Monthly rent'
    assert result.plan_id == '1'
    assert result.start_date == '2025-01-01'
    assert result.plan_type == 'Taksit'
    assert result.frequency == 'Aylık'
    assert result.end_date == '2025-12-31'
    assert result.target_asset_id == 5


@pytest.mark.unit
def test_plan_form_from_request_invalid_amount():
    """Test plan_form_from_request with invalid amount"""
    form = {
        'action': 'add_expense_plan',
        'amount': '0',
        'installments': '12',
        'payment_day': '15',
    }
    
    with pytest.raises(ValueError, match="Tutar ve gün değerleri geçerli olmalıdır"):
        plan_form_from_request(form)


@pytest.mark.unit
def test_plan_form_from_request_invalid_installments():
    """Test plan_form_from_request with negative installments"""
    form = {
        'action': 'add_expense_plan',
        'amount': '1000',
        'installments': '-1',
        'payment_day': '15',
    }
    
    with pytest.raises(ValueError, match="Tutar ve gün değerleri geçerli olmalıdır"):
        plan_form_from_request(form)


@pytest.mark.unit
def test_plan_form_from_request_invalid_payment_day():
    """Test plan_form_from_request with invalid payment day"""
    form = {
        'action': 'add_expense_plan',
        'amount': '1000',
        'installments': '12',
        'payment_day': '0',
    }
    
    with pytest.raises(ValueError, match="Tutar ve gün değerleri geçerli olmalıdır"):
        plan_form_from_request(form)


@pytest.mark.unit
def test_plan_form_from_request_payment_day_too_high():
    """Test plan_form_from_request with payment day > 31"""
    form = {
        'action': 'add_expense_plan',
        'amount': '1000',
        'installments': '12',
        'payment_day': '32',
    }
    
    with pytest.raises(ValueError, match="Tutar ve gün değerleri geçerli olmalıdır"):
        plan_form_from_request(form)


@pytest.mark.unit
def test_plan_form_from_request_invalid_action():
    """Test plan_form_from_request with invalid action"""
    form = {
        'action': 'invalid_action',
        'amount': '1000',
        'installments': '12',
        'payment_day': '15',
    }
    
    with pytest.raises(ValueError, match="Geçersiz işlem"):
        plan_form_from_request(form)


@pytest.mark.unit
def test_plan_form_from_request_invalid_date_format():
    """Test plan_form_from_request with invalid date format"""
    form = {
        'action': 'add_expense_plan',
        'amount': '1000',
        'installments': '12',
        'payment_day': '15',
        'start_date': '01/01/2025',
    }
    
    with pytest.raises(ValueError, match="Geçersiz başlangıç tarihi formatı"):
        plan_form_from_request(form)


@pytest.mark.unit
def test_plan_form_from_request_default_values():
    """Test plan_form_from_request with default values"""
    form = {
        'action': 'add_expense_plan',
        'amount': '1000',
        'installments': '12',
        'payment_day': '15',
    }
    
    result = plan_form_from_request(form)
    assert result.name == ''
    assert result.category == ''
    assert result.note is None
    assert result.plan_id is None
    assert result.start_date is None
    assert result.plan_type == 'Taksit'
    assert result.frequency == 'Aylık'
    assert result.target_asset_id is None


@pytest.mark.unit
def test_payment_form_from_request_success():
    """Test payment_form_from_request with valid data"""
    form = {
        'plan_id': '1',
        'amount': '100',
        'payment_date': '2025-01-15',
        'installment_number': '1',
        'notes': 'First payment',
    }
    
    result = payment_form_from_request(form)
    assert result.plan_id == '1'
    assert result.amount == 100
    assert result.payment_date == '2025-01-15'
    assert result.installment_number == 1
    assert result.notes == 'First payment'


@pytest.mark.unit
def test_payment_form_from_request_missing_plan_id():
    """Test payment_form_from_request without plan_id"""
    form = {
        'amount': '100',
        'payment_date': '2025-01-15',
    }
    
    with pytest.raises(ValueError, match="Ödeme planı belirtilmedi"):
        payment_form_from_request(form)


@pytest.mark.unit
def test_payment_form_from_request_invalid_amount():
    """Test payment_form_from_request with invalid amount"""
    form = {
        'plan_id': '1',
        'amount': '0',
        'payment_date': '2025-01-15',
    }
    
    with pytest.raises(ValueError, match="Geçerli bir ödeme tutarı girin"):
        payment_form_from_request(form)


@pytest.mark.unit
def test_payment_form_from_request_missing_payment_date():
    """Test payment_form_from_request without payment_date"""
    form = {
        'plan_id': '1',
        'amount': '100',
    }
    
    with pytest.raises(ValueError, match="Ödeme tarihi gerekli"):
        payment_form_from_request(form)


@pytest.mark.unit
def test_payment_form_from_request_invalid_date_format():
    """Test payment_form_from_request with invalid date format"""
    form = {
        'plan_id': '1',
        'amount': '100',
        'payment_date': '15/01/2025',
    }
    
    with pytest.raises(ValueError, match="Geçersiz tarih formatı"):
        payment_form_from_request(form)


@pytest.mark.unit
def test_payment_form_from_request_invalid_installment_number():
    """Test payment_form_from_request with invalid installment number"""
    form = {
        'plan_id': '1',
        'amount': '100',
        'payment_date': '2025-01-15',
        'installment_number': '0',
    }
    
    with pytest.raises(ValueError, match="Taksit numarası en az 1 olmalıdır"):
        payment_form_from_request(form)


@pytest.mark.unit
def test_payment_form_from_request_default_values():
    """Test payment_form_from_request with default values"""
    form = {
        'plan_id': '1',
        'amount': '100',
        'payment_date': '2025-01-15',
    }
    
    result = payment_form_from_request(form)
    assert result.installment_number == 1
    assert result.notes is None


@pytest.mark.unit
def test_logbook_entry_from_request_success():
    """Test logbook_entry_from_request with valid data"""
    form = {
        'title': 'Market Analysis',
        'content': 'Detailed analysis of market trends',
        'entry_date': '2025-01-01',
        'category': 'Finansal',
        'sentiment': 'Pozitif',
        'asset_id': '1',
        'transaction_id': '2',
    }
    
    result = logbook_entry_from_request(form)
    assert result.title == 'Market Analysis'
    assert result.content == 'Detailed analysis of market trends'
    assert result.entry_date == '2025-01-01'
    assert result.category == 'Finansal'
    assert result.sentiment == 'Pozitif'
    assert result.asset_id == '1'
    assert result.transaction_id == '2'


@pytest.mark.unit
def test_logbook_entry_from_request_missing_title():
    """Test logbook_entry_from_request without title"""
    form = {
        'content': 'Test content',
        'entry_date': '2025-01-01',
    }
    
    with pytest.raises(ValueError, match="Başlık zorunludur"):
        logbook_entry_from_request(form)


@pytest.mark.unit
def test_logbook_entry_from_request_missing_content():
    """Test logbook_entry_from_request without content"""
    form = {
        'title': 'Test title',
        'entry_date': '2025-01-01',
    }
    
    with pytest.raises(ValueError, match="İçerik zorunludur"):
        logbook_entry_from_request(form)


@pytest.mark.unit
def test_logbook_entry_from_request_missing_date():
    """Test logbook_entry_from_request without entry_date"""
    form = {
        'title': 'Test title',
        'content': 'Test content',
    }
    
    with pytest.raises(ValueError, match="Tarih zorunludur"):
        logbook_entry_from_request(form)


@pytest.mark.unit
def test_logbook_entry_from_request_default_values():
    """Test logbook_entry_from_request with default values"""
    form = {
        'title': 'Test title',
        'content': 'Test content',
        'entry_date': '2025-01-01',
    }
    
    result = logbook_entry_from_request(form)
    assert result.category == 'Finansal'
    assert result.sentiment == 'Nötr'
    assert result.asset_id is None
    assert result.transaction_id is None


@pytest.mark.unit
def test_request_validators_imports():
    """Test that all validator functions can be imported"""
    from validators.request_validators import (
        transaction_form_from_request,
        plan_form_from_request,
        payment_form_from_request,
        logbook_entry_from_request,
    )
    
    assert callable(transaction_form_from_request)
    assert callable(plan_form_from_request)
    assert callable(payment_form_from_request)
    assert callable(logbook_entry_from_request)
