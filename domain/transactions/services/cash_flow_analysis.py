"""
Cash Flow Analysis Service
===========================
Separates cash flow from net worth by properly handling asset transfers
Phase 2: Cash Flow vs Net Worth separation
"""

import logging
from datetime import datetime
from typing import Dict, List

from models import Transaction, db

logger = logging.getLogger(__name__)


class CashFlowAnalyzer:
    """Analyzes cash flow while excluding transfers from income/expense calculations"""

    @staticmethod
    def is_transfer(transaction: Transaction) -> bool:
        """Check if a transaction is a transfer (not actual income/expense)"""
        return transaction.type == 'Transfer'

    @staticmethod
    def get_cash_flow_summary(tenant_id: str = None, start_date: str = None, end_date: str = None) -> Dict:
        """
        Get cash flow summary excluding transfers

        Args:
            tenant_id: Filter by tenant
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)

        Returns:
            Dict with cash flow metrics
        """
        query = Transaction.query.filter_by(is_deleted=False)

        if tenant_id:
            query = query.filter_by(tenant_id=tenant_id)

        if start_date:
            query = query.filter(Transaction.date >= start_date)
        if end_date:
            query = query.filter(Transaction.date <= end_date)

        transactions = query.all()

        # Separate transfers from actual cash flow
        transfers = [t for t in transactions if CashFlowAnalyzer.is_transfer(t)]
        cash_flow_transactions = [t for t in transactions if not CashFlowAnalyzer.is_transfer(t)]

        # Calculate actual cash flow (excluding transfers)
        total_income = sum(t.amount for t in cash_flow_transactions if t.type == 'Gelir' and t.status == 'Ödendi')
        total_expenses = sum(t.amount for t in cash_flow_transactions if t.type == 'Gider' and t.status == 'Ödendi')
        total_investments = sum(t.amount for t in cash_flow_transactions if t.type == 'Yatırım' and t.status == 'Ödendi')

        pending_income = sum(t.amount for t in cash_flow_transactions if t.type == 'Gelir' and t.status == 'Bekliyor')
        pending_expenses = sum(t.amount for t in cash_flow_transactions if t.type == 'Gider' and t.status == 'Bekliyor')

        # Calculate transfers separately
        total_transfers = sum(t.amount for t in transfers if t.status == 'Ödendi')

        # Net cash flow (income - expenses - investments)
        net_cash_flow = total_income - total_expenses - total_investments

        # Net worth change (includes transfers as they move money between accounts)
        net_worth_change = net_cash_flow  # Transfers don't change net worth, just move money

        return {
            'period': {
                'start_date': start_date,
                'end_date': end_date
            },
            'cash_flow': {
                'total_income': total_income,
                'total_expenses': total_expenses,
                'total_investments': total_investments,
                'net_cash_flow': net_cash_flow,
                'pending_income': pending_income,
                'pending_expenses': pending_expenses
            },
            'transfers': {
                'total_transfers': total_transfers,
                'transfer_count': len(transfers),
                'transfers': [
                    {
                        'date': t.date,
                        'amount': t.amount,
                        'from': t.transfer_from,
                        'to': t.transfer_to,
                        'description': t.description
                    }
                    for t in transfers
                ]
            },
            'net_worth': {
                'change': net_worth_change,
                'excludes_transfers': True
            },
            'transaction_counts': {
                'total': len(transactions),
                'cash_flow': len(cash_flow_transactions),
                'transfers': len(transfers)
            }
        }

    @staticmethod
    def get_monthly_cash_flow(tenant_id: str = None, year: int = None, month: int = None) -> Dict:
        """
        Get monthly cash flow analysis excluding transfers

        Args:
            tenant_id: Filter by tenant
            year: Year (default: current year)
            month: Month (default: current month)

        Returns:
            Dict with monthly cash flow breakdown
        """
        if not year:
            year = datetime.now().year
        if not month:
            month = datetime.now().month

        start_date = f"{year}-{month:02d}-01"
        end_date = f"{year}-{month:02d}-31"

        summary = CashFlowAnalyzer.get_cash_flow_summary(tenant_id, start_date, end_date)

        # Add daily breakdown
        query = Transaction.query.filter_by(is_deleted=False)
        if tenant_id:
            query = query.filter_by(tenant_id=tenant_id)

        transactions = query.filter(
            Transaction.date >= start_date,
            Transaction.date <= end_date
        ).all()

        daily_breakdown = {}
        for tx in transactions:
            if tx.date not in daily_breakdown:
                daily_breakdown[tx.date] = {
                    'income': 0,
                    'expenses': 0,
                    'investments': 0,
                    'transfers': 0
                }

            if CashFlowAnalyzer.is_transfer(tx):
                daily_breakdown[tx.date]['transfers'] += tx.amount
            elif tx.type == 'Gelir' and tx.status == 'Ödendi':
                daily_breakdown[tx.date]['income'] += tx.amount
            elif tx.type == 'Gider' and tx.status == 'Ödendi':
                daily_breakdown[tx.date]['expenses'] += tx.amount
            elif tx.type == 'Yatırım' and tx.status == 'Ödendi':
                daily_breakdown[tx.date]['investments'] += tx.amount

        summary['daily_breakdown'] = daily_breakdown
        summary['period']['year'] = year
        summary['period']['month'] = month

        return summary

    @staticmethod
    def create_transfer(
        date: str,
        amount: float,
        from_account: str,
        to_account: str,
        description: str = None,
        note: str = None,
        tenant_id: str = None
    ) -> Transaction:
        """
        Create a transfer transaction (doesn't affect cash flow, only moves money)

        Args:
            date: Transfer date (YYYY-MM-DD)
            amount: Transfer amount
            from_account: Source account
            to_account: Destination account
            description: Description
            note: Note
            tenant_id: Tenant ID

        Returns:
            Transaction instance
        """
        from domain.tenant.context import TenantContext
        tenant_id = tenant_id or TenantContext.optional()

        transfer = Transaction(
            date=date,
            category='Transfer',
            description=description or f'{from_account} → {to_account}',
            note=note,
            type='Transfer',
            status='Ödendi',
            amount=amount,
            transfer_from=from_account,
            transfer_to=to_account,
            tenant_id=tenant_id,
            is_admin_generated=False
        )

        db.session.add(transfer)
        db.session.commit()

        logger.info(f"Transfer created: {amount} from {from_account} to {to_account}")

        return transfer

    @staticmethod
    def get_transfer_history(tenant_id: str = None, limit: int = 50) -> List[Dict]:
        """
        Get transfer history

        Args:
            tenant_id: Filter by tenant
            limit: Maximum number of records

        Returns:
            List of transfer records
        """
        query = Transaction.query.filter_by(type='Transfer', is_deleted=False)

        if tenant_id:
            query = query.filter_by(tenant_id=tenant_id)

        transfers = query.order_by(Transaction.date.desc()).limit(limit).all()

        return [
            {
                'id': t.id,
                'date': t.date,
                'amount': t.amount,
                'from': t.transfer_from,
                'to': t.transfer_to,
                'description': t.description,
                'note': t.note
            }
            for t in transfers
        ]

    @staticmethod
    def compare_with_vs_without_transfers(tenant_id: str = None, start_date: str = None, end_date: str = None) -> Dict:
        """
        Compare cash flow metrics with and without transfers

        This demonstrates the difference between cash flow and net worth
        """
        # Get cash flow excluding transfers (correct cash flow)
        correct_cash_flow = CashFlowAnalyzer.get_cash_flow_summary(tenant_id, start_date, end_date)

        # Get all transactions including transfers (incorrect cash flow if treated as expense)
        query = Transaction.query.filter_by(is_deleted=False)
        if tenant_id:
            query = query.filter_by(tenant_id=tenant_id)
        if start_date:
            query = query.filter(Transaction.date >= start_date)
        if end_date:
            query = query.filter(Transaction.date <= end_date)

        all_transactions = query.all()

        # Incorrect calculation (treating transfers as expenses)
        incorrect_income = sum(t.amount for t in all_transactions if t.type == 'Gelir' and t.status == 'Ödendi')
        incorrect_expenses = sum(t.amount for t in all_transactions if t.type == 'Gider' and t.status == 'Ödendi')
        incorrect_investments = sum(t.amount for t in all_transactions if t.type == 'Yatırım' and t.status == 'Ödendi')
        incorrect_transfers = sum(t.amount for t in all_transactions if t.type == 'Transfer' and t.status == 'Ödendi')

        # If transfers were incorrectly counted as expenses
        incorrect_expenses_with_transfers = incorrect_expenses + incorrect_transfers
        incorrect_net = incorrect_income - incorrect_expenses_with_transfers - incorrect_investments

        return {
            'correct_cash_flow': {
                'income': correct_cash_flow['cash_flow']['total_income'],
                'expenses': correct_cash_flow['cash_flow']['total_expenses'],
                'investments': correct_cash_flow['cash_flow']['total_investments'],
                'net': correct_cash_flow['cash_flow']['net_cash_flow']
            },
            'incorrect_including_transfers': {
                'income': incorrect_income,
                'expenses': incorrect_expenses_with_transfers,
                'investments': incorrect_investments,
                'net': incorrect_net
            },
            'difference': {
                'expense_difference': incorrect_expenses_with_transfers - correct_cash_flow['cash_flow']['total_expenses'],
                'net_difference': incorrect_net - correct_cash_flow['cash_flow']['net_cash_flow'],
                'transfer_amount': incorrect_transfers
            },
            'explanation': 'Transfers move money between accounts but don\'t change net worth. They should be excluded from cash flow analysis.'
        }
