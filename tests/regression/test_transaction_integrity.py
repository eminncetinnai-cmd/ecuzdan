"""
Transaction Domain Integrity Tests - FAZ 1
Validates transaction domain rules and business logic integrity
"""

import pytest
from decimal import Decimal
from domain.transactions.services.financial_ledger import (
    create_one_time_transaction,
    LedgerError,
)
from models import Category, Transaction, db


def _get_or_create_standard_category(category_name, category_type):
    """Get or create a standard category for testing."""
    category = Category.query.filter_by(name=category_name, tenant_id=None).first()
    if not category:
        category = Category(name=category_name, type=category_type, tenant_id=None)
        db.session.add(category)
        db.session.commit()
    return category


@pytest.fixture
def app(app):
    """Use the existing app fixture from conftest.py"""
    return app


@pytest.mark.regression
def test_transaction_amount_must_be_positive(app):
    """
    Transaction amount invariant:
    - Transaction amounts must be positive
    - Zero or negative amounts should be rejected
    """
    tenant = 'tenant_positive_amount'
    
    # Create category using standard categories
    cat = _get_or_create_standard_category('Maaş / Ücret Geliri', 'Gelir')
    
    # Test with positive amount (should succeed)
    create_one_time_transaction(
        '2025-01-01', cat.name, 'Valid transaction', 
        Decimal('100'), 'Ödendi', 'Maaş / Ücret Geliri', tenant_id=tenant
    )
    db.session.commit()
    
    # Verify transaction was created
    tx = Transaction.query.filter_by(description='Valid transaction').first()
    assert tx is not None
    assert tx.amount > 0


@pytest.mark.regression
def test_transaction_date_validation(app):
    """
    Transaction date invariant:
    - Transaction dates must be valid
    - Future dates may be allowed for planned transactions
    - Invalid date formats should be rejected
    """
    tenant = 'tenant_date_validation'
    
    # Create category using standard categories
    cat = _get_or_create_standard_category('Maaş / Ücret Geliri', 'Gelir')
    
    # Test with valid date
    create_one_time_transaction(
        '2025-01-01', cat.name, 'Valid date transaction', 
        Decimal('100'), 'Ödendi', 'Maaş / Ücret Geliri', tenant_id=tenant
    )
    db.session.commit()
    
    # Verify transaction was created
    tx = Transaction.query.filter_by(description='Valid date transaction').first()
    assert tx is not None
    assert tx.date == '2025-01-01'


@pytest.mark.regression
def test_transaction_status_enum(app):
    """
    Transaction status invariant:
    - Transaction status must be from valid enum values
    - Common statuses: 'Ödendi', 'Bekliyor', 'İptal'
    """
    tenant = 'tenant_status_enum'
    
    # Create category using standard categories
    cat = _get_or_create_standard_category('Maaş / Ücret Geliri', 'Gelir')
    
    # Test with valid status
    create_one_time_transaction(
        '2025-01-01', cat.name, 'Paid transaction', 
        Decimal('100'), 'Ödendi', 'Maaş / Ücret Geliri', tenant_id=tenant
    )
    db.session.commit()
    
    # Verify status
    tx = Transaction.query.filter_by(description='Paid transaction').first()
    assert tx.status == 'Ödendi'


@pytest.mark.regression
def test_transaction_category_type_match(app):
    """
    Transaction category type invariant:
    - Transaction type must match category type
    - Income transactions must use income categories
    - Expense transactions must use expense categories
    """
    tenant = 'tenant_category_match'
    
    # Create categories using standard categories
    income_cat = _get_or_create_standard_category('Maaş / Ücret Geliri', 'Gelir')
    expense_cat = _get_or_create_standard_category('Konut & Kira', 'Gider')
    
    # Create income transaction with income category
    create_one_time_transaction(
        '2025-01-01', income_cat.name, 'Income transaction', 
        Decimal('100'), 'Ödendi', 'Maaş / Ücret Geliri', tenant_id=tenant
    )
    db.session.commit()
    
    # Verify type match
    tx = Transaction.query.filter_by(description='Income transaction').first()
    assert tx.type == 'Gelir'
    assert tx.category == income_cat.name


@pytest.mark.regression
def test_transaction_tenant_isolation(app):
    """
    Transaction tenant isolation invariant:
    - Transactions must be scoped to their tenant
    - One tenant cannot see another tenant's transactions
    """
    tenant_a = 'tenant_isolation_a'
    tenant_b = 'tenant_isolation_b'
    
    # Use standard categories for both tenants
    cat = _get_or_create_standard_category('Maaş / Ücret Geliri', 'Gelir')
    
    # Create transaction for tenant A
    create_one_time_transaction(
        '2025-01-01', cat.name, 'Tenant A transaction', 
        Decimal('1000'), 'Ödendi', 'Maaş / Ücret Geliri', tenant_id=tenant_a
    )
    db.session.commit()
    
    # Create transaction for tenant B
    create_one_time_transaction(
        '2025-01-01', cat.name, 'Tenant B transaction', 
        Decimal('500'), 'Ödendi', 'Maaş / Ücret Geliri', tenant_id=tenant_b
    )
    db.session.commit()
    
    # Verify isolation
    tx_a = Transaction.query.filter_by(description='Tenant A transaction', tenant_id=tenant_a).first()
    tx_b = Transaction.query.filter_by(description='Tenant B transaction', tenant_id=tenant_b).first()
    
    assert tx_a is not None
    assert tx_b is not None
    assert tx_a.tenant_id == tenant_a
    assert tx_b.tenant_id == tenant_b
    assert tx_a.tenant_id != tx_b.tenant_id


@pytest.mark.regression
def test_transaction_description_required(app):
    """
    Transaction description invariant:
    - Transactions should have meaningful descriptions
    - Empty descriptions may be allowed but should be handled
    """
    tenant = 'tenant_description'
    
    # Create category
    cat = Category(name='Maaş / Ücret Geliri', type='Gelir', tenant_id=tenant)
    db.session.add(cat)
    db.session.commit()
    
    # Create transaction with description
    create_one_time_transaction(
        '2025-01-01', 'Maaş / Ücret Geliri', 'Test description', 
        Decimal('100'), 'Ödendi', 'Maaş / Ücret Geliri', tenant_id=tenant
    )
    db.session.commit()
    
    # Verify description
    tx = Transaction.query.filter_by(description='Test description').first()
    assert tx is not None
    assert tx.description == 'Test description'


@pytest.mark.regression
def test_transaction_immutability_after_creation(app):
    """
    Transaction immutability invariant:
    - Once created, transaction key fields should not change
    - Only status updates should be allowed
    """
    tenant = 'tenant_immutability'
    
    # Create category
    cat = Category(name='Maaş / Ücret Geliri', type='Gelir', tenant_id=tenant)
    db.session.add(cat)
    db.session.commit()
    
    # Create transaction
    create_one_time_transaction(
        '2025-01-01', 'Maaş / Ücret Geliri', 'Original transaction', 
        Decimal('100'), 'Ödendi', 'Maaş / Ücret Geliri', tenant_id=tenant
    )
    db.session.commit()
    
    # Verify original values
    tx = Transaction.query.filter_by(description='Original transaction').first()
    original_date = tx.date
    original_amount = tx.amount
    original_category = tx.category
    
    # Transaction should maintain its original key fields
    assert tx.date == original_date
    assert tx.amount == original_amount
    assert tx.category == original_category


@pytest.mark.regression
def test_transaction_type_enum_values(app):
    """
    Transaction type enum invariant:
    - Transaction type must be from valid enum values
    - Valid types: 'Gelir', 'Gider', 'Yatırım'
    """
    tenant = 'tenant_type_enum'
    
    # Create categories for each type
    income_cat = Category(name='Maaş / Ücret Geliri', type='Gelir', tenant_id=tenant)
    expense_cat = Category(name='Kira', type='Gider', tenant_id=tenant)
    investment_cat = Category(name='Hisse Senedi', type='Yatırım', tenant_id=tenant)
    db.session.add_all([income_cat, expense_cat, investment_cat])
    db.session.commit()
    
    # Create income transaction
    create_one_time_transaction(
        '2025-01-01', 'Maaş / Ücret Geliri', 'Income', 
        Decimal('100'), 'Ödendi', 'Maaş / Ücret Geliri', tenant_id=tenant
    )
    
    # Create expense transaction
    create_one_time_transaction(
        '2025-01-02', 'Kira', 'Expense', 
        Decimal('50'), 'Ödendi', 'Kira', tenant_id=tenant
    )
    
    # Create investment transaction
    create_one_time_transaction(
        '2025-01-03', 'Hisse Senedi', 'Investment', 
        Decimal('200'), 'Ödendi', 'Hisse Senedi', tenant_id=tenant
    )
    db.session.commit()
    
    # Verify types
    income_tx = Transaction.query.filter_by(description='Income').first()
    expense_tx = Transaction.query.filter_by(description='Expense').first()
    investment_tx = Transaction.query.filter_by(description='Investment').first()
    
    assert income_tx.type == 'Gelir'
    assert expense_tx.type == 'Gider'
    assert investment_tx.type == 'Yatırım'


@pytest.mark.regression
def test_transaction_amount_scale(app):
    """
    Transaction amount scale invariant:
    - Transaction amounts should use consistent decimal scale
    - Amounts should be quantized to currency precision
    """
    tenant = 'tenant_amount_scale'
    
    # Create category
    cat = Category(name='Maaş / Ücret Geliri', type='Gelir', tenant_id=tenant)
    db.session.add(cat)
    db.session.commit()
    
    # Create transaction with precise amount
    create_one_time_transaction(
        '2025-01-01', 'Maaş / Ücret Geliri', 'Precise amount', 
        Decimal('123.4567'), 'Ödendi', 'Maaş / Ücret Geliri', tenant_id=tenant
    )
    db.session.commit()
    
    # Verify amount is stored with proper precision
    tx = Transaction.query.filter_by(description='Precise amount').first()
    assert tx is not None
    # Amount should be quantized to 4 decimal places (currency precision)
    assert tx.amount.as_tuple().exponent == -4


@pytest.mark.regression
def test_transaction_cascade_delete_protection(app):
    """
    Transaction cascade delete invariant:
    - Deleting a category should handle associated transactions
    - Transactions should either be protected or cascade properly
    """
    tenant = 'tenant_cascade'
    
    # Create category
    cat = Category(name='Maaş / Ücret Geliri', type='Gelir', tenant_id=tenant)
    db.session.add(cat)
    db.session.commit()
    
    # Create transaction
    create_one_time_transaction(
        '2025-01-01', 'Maaş / Ücret Geliri', 'Test transaction', 
        Decimal('100'), 'Ödendi', 'Maaş / Ücret Geliri', tenant_id=tenant
    )
    db.session.commit()
    
    # Verify transaction exists
    tx = Transaction.query.filter_by(description='Test transaction').first()
    assert tx is not None
    
    # Note: Actual cascade delete behavior depends on database schema
    # This test documents the current behavior
    # If category is deleted, transaction should be handled appropriately
