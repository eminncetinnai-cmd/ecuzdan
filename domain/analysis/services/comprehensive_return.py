"""
Comprehensive Return Calculation Service
========================================
Total return calculation including dividends, coupons, interest, FX gains
Phase 6: Comprehensive return calculation (dividends, coupons, interest, FX gains)
"""

import logging
from datetime import datetime
from typing import Dict

from models import Asset, Transaction, db

from .multi_currency import CurrencyManager

logger = logging.getLogger(__name__)


class ComprehensiveReturnCalculator:
    """Comprehensive return calculation including all income sources"""

    @staticmethod
    def calculate_total_return(asset: Asset, start_date: str = None, end_date: str = None) -> Dict:
        """
        Calculate comprehensive total return including:
        - Price appreciation
        - Dividends
        - Interest
        - Coupons
        - FX gains
        - Other income

        Formula: Total Return = (Price Gain + Dividends + Interest + Coupons + FX Gains) / Cost

        Args:
            asset: Asset instance
            start_date: Start date
            end_date: End date

        Returns:
            Dict with comprehensive return breakdown
        """
        if not start_date:
            start_date = asset.purchase_date
        if not end_date:
            end_date = datetime.now().strftime('%Y-%m-%d')

        # Price appreciation
        price_gain = asset.value - asset.purchase_cost
        price_return_pct = (price_gain / asset.purchase_cost * 100) if asset.purchase_cost > 0 else 0

        # Income components
        dividends = ComprehensiveReturnCalculator._get_dividend_income(asset, start_date, end_date)
        interest = ComprehensiveReturnCalculator._get_interest_income(asset, start_date, end_date)
        coupons = ComprehensiveReturnCalculator._get_coupon_income(asset, start_date, end_date)
        fx_gains = ComprehensiveReturnCalculator._get_fx_gains(asset, start_date, end_date)
        other_income = ComprehensiveReturnCalculator._get_other_income(asset, start_date, end_date)

        # Total income
        total_income = dividends + interest + coupons + fx_gains + other_income

        # Total gain
        total_gain = price_gain + total_income

        # Total return percentage
        total_return_pct = (total_gain / asset.purchase_cost * 100) if asset.purchase_cost > 0 else 0

        # Income yield (annualized)
        holding_days = ComprehensiveReturnCalculator._days_between(start_date, end_date)
        income_yield = (total_income / asset.purchase_cost * 100) if asset.purchase_cost > 0 else 0
        annualized_yield = (income_yield * (365 / holding_days)) if holding_days > 0 else 0

        return {
            'period': {
                'start_date': start_date,
                'end_date': end_date,
                'holding_days': holding_days
            },
            'price_appreciation': {
                'gain': price_gain,
                'return_pct': price_return_pct
            },
            'income_components': {
                'dividends': dividends,
                'interest': interest,
                'coupons': coupons,
                'fx_gains': fx_gains,
                'other_income': other_income,
                'total_income': total_income
            },
            'total_return': {
                'total_gain': total_gain,
                'total_return_pct': total_return_pct,
                'income_yield': income_yield,
                'annualized_yield': annualized_yield
            },
            'return_breakdown': {
                'price_contribution_pct': (price_gain / total_gain * 100) if total_gain > 0 else 0,
                'income_contribution_pct': (total_income / total_gain * 100) if total_gain > 0 else 0
            }
        }

    @staticmethod
    def _get_dividend_income(asset: Asset, start_date: str, end_date: str) -> float:
        """Get dividend income from transactions"""
        # Look for dividend transactions (Temettü category)
        dividend_tx = Transaction.query.filter(
            Transaction.source_id == asset.id,
            Transaction.source_type == 'asset_dividend',
            Transaction.type == 'Gelir',
            Transaction.date >= start_date,
            Transaction.date <= end_date,
            not Transaction.is_deleted
        ).all()

        return sum(tx.amount for tx in dividend_tx)

    @staticmethod
    def _get_interest_income(asset: Asset, start_date: str, end_date: str) -> float:
        """Get interest income from transactions"""
        # Look for interest transactions (Faiz category)
        interest_tx = Transaction.query.filter(
            Transaction.source_id == asset.id,
            Transaction.source_type == 'asset_interest',
            Transaction.type == 'Gelir',
            Transaction.date >= start_date,
            Transaction.date <= end_date,
            not Transaction.is_deleted
        ).all()

        return sum(tx.amount for tx in interest_tx)

    @staticmethod
    def _get_coupon_income(asset: Asset, start_date: str, end_date: str) -> float:
        """Get coupon income from bond transactions"""
        # Look for coupon transactions (Kupon category)
        coupon_tx = Transaction.query.filter(
            Transaction.source_id == asset.id,
            Transaction.source_type == 'asset_coupon',
            Transaction.type == 'Gelir',
            Transaction.date >= start_date,
            Transaction.date <= end_date,
            not Transaction.is_deleted
        ).all()

        return sum(tx.amount for tx in coupon_tx)

    @staticmethod
    def _get_fx_gains(asset: Asset, start_date: str, end_date: str) -> float:
        """Get FX gains from currency fluctuations"""
        # Calculate FX gain based on currency change
        if not hasattr(asset, 'original_currency') or asset.currency == 'TRY':
            return 0.0

        # Get historical and current exchange rates
        original_rate = CurrencyManager.get_exchange_rate(asset.currency, 'TRY', start_date)
        current_rate = CurrencyManager.get_exchange_rate(asset.currency, 'TRY', end_date)

        # FX gain on original cost
        original_cost_try = asset.purchase_cost * original_rate
        current_cost_try = asset.purchase_cost * current_rate
        fx_gain = current_cost_try - original_cost_try

        return fx_gain

    @staticmethod
    def _get_other_income(asset: Asset, start_date: str, end_date: str) -> float:
        """Get other income from transactions"""
        # Look for other income transactions
        other_tx = Transaction.query.filter(
            Transaction.source_id == asset.id,
            Transaction.source_type == 'asset_other',
            Transaction.type == 'Gelir',
            Transaction.date >= start_date,
            Transaction.date <= end_date,
            not Transaction.is_deleted
        ).all()

        return sum(tx.amount for tx in other_tx)

    @staticmethod
    def _days_between(date1: str, date2: str) -> int:
        """Calculate days between two dates"""
        d1 = datetime.strptime(date1, '%Y-%m-%d')
        d2 = datetime.strptime(date2, '%Y-%m-%d')
        return (d2 - d1).days

    @staticmethod
    def record_dividend_payment(asset_id: int, amount: float, payment_date: str, note: str = None, tenant_id: str = None) -> Transaction:
        """
        Record a dividend payment for an asset

        Args:
            asset_id: Asset ID
            amount: Dividend amount
            payment_date: Payment date
            note: Note
            tenant_id: Tenant ID

        Returns:
            Transaction instance
        """
        from flask import g
        tenant_id = tenant_id or g.get('tenant_id')

        dividend_tx = Transaction(
            date=payment_date,
            category='Temettü',
            description='Temettü Ödemesi',
            note=note,
            type='Gelir',
            amount=amount,
            status='Ödendi',
            source_id=asset_id,
            source_type='asset_dividend',
            tenant_id=tenant_id,
            is_admin_generated=False
        )

        db.session.add(dividend_tx)
        db.session.commit()

        logger.info(f"Dividend payment recorded: {amount} for asset {asset_id}")

        return dividend_tx

    @staticmethod
    def record_interest_payment(asset_id: int, amount: float, payment_date: str, note: str = None, tenant_id: str = None) -> Transaction:
        """
        Record an interest payment for an asset

        Args:
            asset_id: Asset ID
            amount: Interest amount
            payment_date: Payment date
            note: Note
            tenant_id: Tenant ID

        Returns:
            Transaction instance
        """
        from flask import g
        tenant_id = tenant_id or g.get('tenant_id')

        interest_tx = Transaction(
            date=payment_date,
            category='Faiz',
            description='Faiz Ödemesi',
            note=note,
            type='Gelir',
            amount=amount,
            status='Ödendi',
            source_id=asset_id,
            source_type='asset_interest',
            tenant_id=tenant_id,
            is_admin_generated=False
        )

        db.session.add(interest_tx)
        db.session.commit()

        logger.info(f"Interest payment recorded: {amount} for asset {asset_id}")

        return interest_tx

    @staticmethod
    def get_portfolio_total_return(tenant_id: str = None, start_date: str = None, end_date: str = None) -> Dict:
        """
        Get portfolio-level comprehensive return

        Args:
            tenant_id: Filter by tenant
            start_date: Start date
            end_date: End date

        Returns:
            Dict with portfolio comprehensive return
        """
        query = Asset.query
        if tenant_id:
            query = query.filter_by(tenant_id=tenant_id)

        assets = query.all()

        if not assets:
            return {
                'total_assets': 0,
                'total_cost': 0,
                'total_value': 0,
                'total_income': 0,
                'total_return': 0,
                'asset_returns': []
            }

        total_cost = sum(a.purchase_cost for a in assets)
        total_value = sum(a.value for a in assets)

        asset_returns = []
        total_income = 0

        for asset in assets:
            asset_return = ComprehensiveReturnCalculator.calculate_total_return(asset, start_date, end_date)
            asset_returns.append({
                'asset_id': asset.id,
                'asset_name': asset.name,
                'asset_type': asset.type,
                'return': asset_return
            })
            total_income += asset_return['income_components']['total_income']

        total_gain = (total_value - total_cost) + total_income
        total_return_pct = (total_gain / total_cost * 100) if total_cost > 0 else 0

        return {
            'total_assets': len(assets),
            'total_cost': total_cost,
            'total_value': total_value,
            'total_income': total_income,
            'total_gain': total_gain,
            'total_return_pct': total_return_pct,
            'asset_returns': asset_returns,
            'period': {
                'start_date': start_date,
                'end_date': end_date
            }
        }

    @staticmethod
    def compare_simple_vs_comprehensive_return(asset: Asset, start_date: str = None, end_date: str = None) -> Dict:
        """
        Compare simple return vs comprehensive return

        This demonstrates why comprehensive calculation matters
        """
        # Simple return (price only)
        simple_return = ((asset.value - asset.purchase_cost) / asset.purchase_cost * 100) if asset.purchase_cost > 0 else 0

        # Comprehensive return (all sources)
        comprehensive = ComprehensiveReturnCalculator.calculate_total_return(asset, start_date, end_date)

        difference = comprehensive['total_return']['total_return_pct'] - simple_return
        income_contribution = comprehensive['income_components']['total_income']

        return {
            'simple_return': simple_return,
            'comprehensive_return': comprehensive['total_return']['total_return_pct'],
            'difference': difference,
            'income_contribution': income_contribution,
            'income_breakdown': comprehensive['income_components'],
            'explanation': f"Comprehensive return includes {income_contribution} in income (dividends, interest, etc.) that simple return misses."
        }
