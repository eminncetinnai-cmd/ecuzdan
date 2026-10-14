"""Tenant-scoped, read-only reconciliation domain service.

This module owns reconciliation semantics. HTTP routes only validate transport
and serialize errors; no calculation is duplicated in templates or routes.
"""

from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation

from domain.reconciliation.models import BankAccount, BankStatementSnapshot
from domain.transactions.models import Transaction
from shared.decimal_precision import to_decimal

_ZERO = Decimal('0')
_TOLERANCE = Decimal('0.01')
_QUANTUM = Decimal('0.0001')


class ReconciliationInputError(ValueError):
    """Raised when a reconciliation request cannot be safely interpreted."""


class ReconciliationAccountNotFoundError(ReconciliationInputError):
    """Raised without revealing whether another tenant owns an account id."""


def _fmt(value):
    return str(to_decimal(value).quantize(_QUANTUM)) if value is not None else None


def _amount(item):
    return to_decimal(item.amount or 0)


def _signed_cash(item):
    if item.type == 'Gelir':
        return _amount(item)
    if item.type in ('Gider', 'Yatırım'):
        return -_amount(item)
    # Transferler iki hesap arasında nakit nötrdür. Mevcut transfer_from /
    # transfer_to alanları string olduğu için bu servis otomatik bakiye üretmez.
    return _ZERO


def _total(items):
    return sum((_signed_cash(item) for item in items), _ZERO)


def _serialize_account(account):
    return {
        'id': account.id,
        'name': account.name,
        'institution': account.institution,
        'account_type': account.account_type,
        'currency': account.currency,
        'is_active': bool(account.is_active),
        'created_at': account.created_at.isoformat() if account.created_at else None,
    }


def parse_reconciliation_params(args):
    """Parse and validate common GET parameters without touching the database."""
    as_of = args.get('as_of') or datetime.now(timezone.utc).strftime('%Y-%m-%d')
    try:
        parsed_as_of = datetime.strptime(as_of, '%Y-%m-%d')
    except (TypeError, ValueError) as exc:
        raise ReconciliationInputError('as_of YYYY-MM-DD formatında olmalıdır') from exc
    if parsed_as_of.strftime('%Y-%m-%d') != as_of:
        raise ReconciliationInputError('as_of YYYY-MM-DD formatında olmalıdır')

    statement_raw = args.get('statement_balance')
    statement_balance = None
    if statement_raw not in (None, ''):
        try:
            statement_balance = to_decimal(statement_raw)
        except (InvalidOperation, TypeError, ValueError) as exc:
            raise ReconciliationInputError('statement_balance geçerli bir sayı olmalıdır') from exc
        if not statement_balance.is_finite():
            raise ReconciliationInputError('statement_balance sonlu bir sayı olmalıdır')

    try:
        pending_limit = int(args.get('pending_limit', '50'))
    except (TypeError, ValueError) as exc:
        raise ReconciliationInputError('pending_limit tam sayı olmalıdır') from exc
    if not 1 <= pending_limit <= 200:
        raise ReconciliationInputError('pending_limit 1 ile 200 arasında olmalıdır')

    account_raw = args.get('account_id')
    account_id = None
    if account_raw not in (None, ''):
        try:
            account_id = int(account_raw)
        except (TypeError, ValueError) as exc:
            raise ReconciliationInputError('account_id tam sayı olmalıdır') from exc
        if account_id < 1:
            raise ReconciliationInputError('account_id pozitif olmalıdır')

    currency = (args.get('currency') or '').strip().upper() or None
    if currency is not None and (len(currency) != 3 or not currency.isalpha()):
        raise ReconciliationInputError('currency ISO 4217 formatında olmalıdır')

    return {
        'as_of': as_of,
        'statement_balance': statement_balance,
        'pending_limit': pending_limit,
        'account_id': account_id,
        'currency': currency,
    }


def list_bank_accounts(tenant_id):
    """Return active accounts in deterministic UI order, scoped to one tenant."""
    return BankAccount.query.filter_by(
        tenant_id=tenant_id,
        is_active=True,
    ).order_by(BankAccount.name.asc(), BankAccount.id.asc()).all()


def _latest_snapshot(account_id, as_of):
    return BankStatementSnapshot.query.filter(
        BankStatementSnapshot.bank_account_id == account_id,
        BankStatementSnapshot.as_of <= as_of,
    ).order_by(
        BankStatementSnapshot.as_of.desc(),
        BankStatementSnapshot.id.desc(),
    ).first()


def _resolve_statement(account_ids, as_of, explicit_balance):
    if explicit_balance is not None:
        return {
            'balance': explicit_balance,
            'source': 'request',
            'as_of': as_of,
            'snapshot_id': None,
            'missing_account_ids': [],
            'snapshot_ids': [],
        }

    snapshots = [_latest_snapshot(account_id, as_of) for account_id in account_ids]
    present = [snapshot for snapshot in snapshots if snapshot is not None]
    missing_ids = [account_id for account_id, snapshot in zip(account_ids, snapshots) if snapshot is None]
    if not present or missing_ids:
        return {
            'balance': None,
            'source': None,
            'as_of': None,
            'snapshot_id': None,
            'missing_account_ids': missing_ids,
            'snapshot_ids': [snapshot.id for snapshot in present],
        }
    currencies = {snapshot.currency for snapshot in present}
    if len(currencies) != 1:
        return {
            'balance': None,
            'source': None,
            'as_of': None,
            'snapshot_id': None,
            'missing_account_ids': list(account_ids),
            'snapshot_ids': [],
        }
    return {
        'balance': sum((to_decimal(snapshot.balance) for snapshot in present), _ZERO),
        'source': 'saved_snapshot',
        'as_of': max(snapshot.as_of for snapshot in present),
        'snapshot_id': present[0].id if len(present) == 1 else None,
        'missing_account_ids': [],
        'snapshot_ids': [snapshot.id for snapshot in present],
    }


def _base_empty_payload(as_of, accounts, scope, currency, status_code, issues, recommendations):
    return {
        'success': True,
        'as_of': as_of,
        'status_code': status_code,
        'explainable': False,
        'tolerance': _fmt(_TOLERANCE),
        'transaction_count': 0,
        'cleared_count': 0,
        'pending_count': 0,
        'income': _fmt(_ZERO),
        'expense': _fmt(_ZERO),
        'investment': _fmt(_ZERO),
        'book_balance': _fmt(_ZERO),
        'cleared_balance': _fmt(_ZERO),
        'pending_net': _fmt(_ZERO),
        'statement_balance': None,
        'difference': None,
        'reconciled': False,
        'pending_summary': {
            'count': 0,
            'income': _fmt(_ZERO),
            'outflow': _fmt(_ZERO),
            'net': _fmt(_ZERO),
            'oldest_date': None,
        },
        'pending_items': [],
        'pending_has_more': False,
        'issues': issues,
        'recommendations': recommendations,
        'scope': scope,
        'currency': currency,
        'account_id': accounts[0].id if len(accounts) == 1 else None,
        'account_ids': [account.id for account in accounts],
        'account': _serialize_account(accounts[0]) if len(accounts) == 1 else None,
        'accounts': [_serialize_account(account) for account in accounts],
        'statement_source': None,
        'statement_as_of': None,
        'statement_snapshot_id': None,
        'statement_snapshot_ids': [],
        'statement_coverage': {
            'complete': False,
            'accounts_with_statement': 0,
            'accounts_missing_statement': [account.id for account in accounts],
        },
        'unassigned_count': 0,
        'currency_groups': [],
    }


def build_reconciliation(
    tenant_id,
    *,
    as_of,
    statement_balance=None,
    pending_limit=50,
    bank_account_id=None,
    currency=None,
    include_unassigned=False,
):
    """Build a deterministic read-only reconciliation worksheet.

    ``include_unassigned=True`` is used only by the legacy endpoint so its
    historical tenant-wide contract remains intact. The standalone workflow
    never silently includes unassigned transactions.
    """
    all_accounts = list_bank_accounts(tenant_id)
    if bank_account_id is not None:
        selected = next((account for account in all_accounts if account.id == bank_account_id), None)
        if selected is None:
            raise ReconciliationAccountNotFoundError('Banka hesabı bulunamadı.')
        accounts = [selected]
        scope = 'account'
        resolved_currency = currency or selected.currency
    else:
        accounts = [account for account in all_accounts if not currency or account.currency == currency]
        scope = 'all_accounts'
        resolved_currency = currency
        currencies = sorted({account.currency for account in all_accounts})
        if not currency and len(currencies) > 1:
            payload = _base_empty_payload(
                as_of,
                all_accounts,
                scope,
                None,
                'currency_selection_required',
                [{'code': 'CURRENCY_SELECTION_REQUIRED', 'severity': 'info'}],
                ['SELECT_CURRENCY'],
            )
            payload['currency_groups'] = [
                {
                    'currency': group_currency,
                    'account_count': sum(1 for account in all_accounts if account.currency == group_currency),
                    'account_ids': [account.id for account in all_accounts if account.currency == group_currency],
                }
                for group_currency in currencies
            ]
            return payload

    if not all_accounts and not include_unassigned:
        return _base_empty_payload(
            as_of,
            [],
            'all_accounts',
            resolved_currency,
            'no_accounts',
            [{'code': 'NO_BANK_ACCOUNTS', 'severity': 'info'}],
            ['ADD_BANK_ACCOUNT'],
        )
    if not accounts and not include_unassigned:
        return _base_empty_payload(
            as_of,
            [],
            scope,
            resolved_currency,
            'account_not_found',
            [{'code': 'ACCOUNT_NOT_FOUND', 'severity': 'warning'}],
            ['SELECT_ACCOUNT'],
        )

    account_ids = [account.id for account in accounts]
    statement = _resolve_statement(account_ids, as_of, statement_balance) if account_ids else {
        'balance': statement_balance,
        'source': 'request' if statement_balance is not None else None,
        'as_of': as_of if statement_balance is not None else None,
        'snapshot_id': None,
        'snapshot_ids': [],
        'missing_account_ids': [],
    }

    query = Transaction.query.filter(
        Transaction.tenant_id == tenant_id,
        Transaction.is_deleted.is_(False),
        Transaction.date <= as_of,
        Transaction.status != 'İptal',
    )
    if account_ids:
        query = query.filter(Transaction.bank_account_id.in_(account_ids))
    elif not include_unassigned:
        query = query.filter(Transaction.bank_account_id.isnot(None))
    transactions = query.order_by(Transaction.date.asc(), Transaction.id.asc()).all()

    unassigned_count = Transaction.query.filter(
        Transaction.tenant_id == tenant_id,
        Transaction.is_deleted.is_(False),
        Transaction.date <= as_of,
        Transaction.status != 'İptal',
        Transaction.bank_account_id.is_(None),
    ).count()

    income = sum((_amount(item) for item in transactions if item.type == 'Gelir'), _ZERO)
    expense = sum((_amount(item) for item in transactions if item.type == 'Gider'), _ZERO)
    investment = sum((_amount(item) for item in transactions if item.type == 'Yatırım'), _ZERO)
    cleared = [item for item in transactions if item.status == 'Ödendi']
    pending = [item for item in transactions if item.status != 'Ödendi']
    book_balance = _total(transactions)
    cleared_balance = _total(cleared)
    pending_net = _total(pending)
    difference = statement['balance'] - book_balance if statement['balance'] is not None else None

    pending_income = sum((_amount(item) for item in pending if item.type == 'Gelir'), _ZERO)
    pending_outflow = sum((_amount(item) for item in pending if item.type in ('Gider', 'Yatırım')), _ZERO)
    pending_items = [
        {
            'id': item.id,
            'date': item.date,
            'category': item.category,
            'description': item.description,
            'type': item.type,
            'status': item.status,
            'amount': str(_amount(item)),
            'signed_amount': str(_signed_cash(item)),
            'source_type': item.source_type,
            'bank_account_id': item.bank_account_id,
        }
        for item in pending[:pending_limit]
    ]

    exact_match = difference is not None and abs(difference) <= _TOLERANCE
    explained_by_pending = (
        difference is not None
        and abs(difference + pending_net) <= _TOLERANCE
        and bool(pending)
    )
    issues = []
    recommendations = []
    if statement['balance'] is None:
        status_code = 'statement_required'
        issues.append({'code': 'STATEMENT_BALANCE_REQUIRED', 'severity': 'info'})
        recommendations.append('ENTER_STATEMENT_BALANCE')
    elif exact_match:
        status_code = 'reconciled'
    elif explained_by_pending:
        status_code = 'explained_by_pending'
        issues.append({
            'code': 'PENDING_TIMING_DIFFERENCE',
            'severity': 'info',
            'amount': _fmt(pending_net),
            'transaction_count': len(pending),
        })
        recommendations.append('REVIEW_PENDING_TRANSACTIONS')
    else:
        status_code = 'unexplained_variance'
        issues.append({'code': 'UNEXPLAINED_VARIANCE', 'severity': 'warning', 'amount': _fmt(difference)})
        recommendations.extend(['REVIEW_PENDING_TRANSACTIONS', 'INSPECT_TRANSACTION_EXCEPTIONS'])

    if scope == 'account' and unassigned_count:
        issues.append({'code': 'UNASSIGNED_TRANSACTIONS', 'severity': 'info', 'count': unassigned_count})
        recommendations.append('ASSIGN_TRANSACTIONS_TO_ACCOUNT')

    return {
        'success': True,
        'as_of': as_of,
        'status_code': status_code,
        'explainable': explained_by_pending or exact_match,
        'tolerance': _fmt(_TOLERANCE),
        'transaction_count': len(transactions),
        'cleared_count': len(cleared),
        'pending_count': len(pending),
        'income': _fmt(income),
        'expense': _fmt(expense),
        'investment': _fmt(investment),
        'book_balance': _fmt(book_balance),
        'cleared_balance': _fmt(cleared_balance),
        'pending_net': _fmt(pending_net),
        'statement_balance': _fmt(statement['balance']),
        'difference': _fmt(difference),
        'reconciled': exact_match,
        'pending_summary': {
            'count': len(pending),
            'income': _fmt(pending_income),
            'outflow': _fmt(pending_outflow),
            'net': _fmt(pending_net),
            'oldest_date': pending[0].date if pending else None,
        },
        'pending_items': pending_items,
        'pending_has_more': len(pending) > pending_limit,
        'issues': issues,
        'recommendations': list(dict.fromkeys(recommendations)),
        'scope': scope,
        'currency': resolved_currency,
        'account_id': accounts[0].id if scope == 'account' else None,
        'account_ids': account_ids,
        'account': _serialize_account(accounts[0]) if scope == 'account' else None,
        'accounts': [_serialize_account(account) for account in accounts],
        'statement_source': statement['source'],
        'statement_as_of': statement['as_of'],
        'statement_snapshot_id': statement['snapshot_id'],
        'statement_snapshot_ids': statement['snapshot_ids'],
        'statement_coverage': {
            'complete': not statement['missing_account_ids'],
            'accounts_with_statement': len(account_ids) - len(statement['missing_account_ids']),
            'accounts_missing_statement': statement['missing_account_ids'],
        },
        'unassigned_count': unassigned_count,
        'currency_groups': [],
    }


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


def list_statement_snapshots(bank_account_id, tenant_id, limit=20):
    """Return statement snapshots for an account in reverse chronological order."""
    return BankStatementSnapshot.query.filter_by(
        tenant_id=tenant_id,
        bank_account_id=bank_account_id,
    ).order_by(
        BankStatementSnapshot.as_of.desc(),
        BankStatementSnapshot.id.desc(),
    ).limit(limit).all()


def save_statement_snapshot(tenant_id, bank_account_id, as_of, balance, currency, note=None, source='manual'):
    """Create or update a statement snapshot."""
    from shared.db import db
    snapshot = BankStatementSnapshot.query.filter_by(
        tenant_id=tenant_id,
        bank_account_id=bank_account_id,
        as_of=as_of,
        currency=currency,
    ).first()
    if snapshot:
        snapshot.balance = balance
        snapshot.note = str(note or '').strip()[:300] or None
        snapshot.source = source
    else:
        snapshot = BankStatementSnapshot(
            tenant_id=tenant_id,
            bank_account_id=bank_account_id,
            as_of=as_of,
            balance=balance,
            currency=currency,
            note=str(note or '').strip()[:300] or None,
            source=source,
        )
        db.session.add(snapshot)
    db.session.commit()
    return snapshot
