"""Tenant-scoped bank accounts domain service.

Manages BankAccount queries and persistence scoped to tenants.
"""

from domain.reconciliation.models import BankAccount


def list_bank_accounts(tenant_id):
    """Return active accounts in deterministic UI order, scoped to one tenant."""
    return BankAccount.query.filter_by(
        tenant_id=tenant_id,
        is_active=True,
    ).order_by(BankAccount.name.asc(), BankAccount.id.asc()).all()


def get_bank_account(account_id, tenant_id):
    """Return active bank account scoped to tenant."""
    return BankAccount.query.filter_by(
        id=account_id,
        tenant_id=tenant_id,
        is_active=True,
    ).first()


def create_bank_account(tenant_id, name, institution, account_type, currency, created_by=None):
    """Create a new bank account scoped to tenant."""
    from shared.db import db
    account = BankAccount(
        tenant_id=tenant_id,
        name=name,
        institution=institution,
        account_type=account_type,
        currency=currency,
        created_by=created_by,
    )
    db.session.add(account)
    db.session.commit()
    return account
