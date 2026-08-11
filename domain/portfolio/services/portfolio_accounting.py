"""
Advanced Portfolio Accounting Service
====================================
FIFO/LIFO cost methods, realized/unrealized gains, tax cost tracking
"""

import logging
from datetime import datetime
from typing import Dict, List, Tuple

from models import Asset, AssetTransaction

logger = logging.getLogger(__name__)


class CostMethod:
    """Cost calculation methods"""
    FIFO = 'FIFO'  # First In, First Out
    LIFO = 'LIFO'  # Last In, First Out
    WEIGHTED_AVERAGE = 'WEIGHTED_AVERAGE'  # Weighted Average Cost
    HIFO = 'HIFO'  # Highest In, First Out (tax optimization)


class PortfolioAccounting:
    """Advanced portfolio accounting with multiple cost methods"""

    @staticmethod
    def get_cost_method(asset: Asset) -> str:
        """Get the cost method for an asset (default: WEIGHTED_AVERAGE)"""
        # Check if asset has a cost_method preference, otherwise use default
        return getattr(asset, 'cost_method', CostMethod.WEIGHTED_AVERAGE)

    @staticmethod
    def calculate_fifo_cost(asset: Asset, sell_quantity: float) -> Tuple[float, List[Dict]]:
        """
        Calculate cost using FIFO method

        Returns:
            Tuple of (total_cost, lot_details)
            lot_details: List of {'quantity': float, 'unit_cost': float, 'total_cost': float, 'buy_date': str}
        """
        transactions = AssetTransaction.query.filter_by(
            asset_id=asset.id,
            transaction_type='buy'
        ).order_by(AssetTransaction.transaction_date.asc()).all()

        remaining_to_sell = sell_quantity
        total_cost = 0.0
        lot_details = []

        for tx in transactions:
            if remaining_to_sell <= 0:
                break

            if tx.quantity > 0:
                quantity_from_lot = min(tx.quantity, remaining_to_sell)
                cost_from_lot = quantity_from_lot * tx.unit_price
                total_cost += cost_from_lot

                lot_details.append({
                    'quantity': quantity_from_lot,
                    'unit_cost': tx.unit_price,
                    'total_cost': cost_from_lot,
                    'buy_date': tx.transaction_date,
                    'transaction_id': tx.id
                })

                remaining_to_sell -= quantity_from_lot

        return total_cost, lot_details

    @staticmethod
    def calculate_lifo_cost(asset: Asset, sell_quantity: float) -> Tuple[float, List[Dict]]:
        """
        Calculate cost using LIFO method

        Returns:
            Tuple of (total_cost, lot_details)
        """
        transactions = AssetTransaction.query.filter_by(
            asset_id=asset.id,
            transaction_type='buy'
        ).order_by(AssetTransaction.transaction_date.desc()).all()

        remaining_to_sell = sell_quantity
        total_cost = 0.0
        lot_details = []

        for tx in transactions:
            if remaining_to_sell <= 0:
                break

            if tx.quantity > 0:
                quantity_from_lot = min(tx.quantity, remaining_to_sell)
                cost_from_lot = quantity_from_lot * tx.unit_price
                total_cost += cost_from_lot

                lot_details.append({
                    'quantity': quantity_from_lot,
                    'unit_cost': tx.unit_price,
                    'total_cost': cost_from_lot,
                    'buy_date': tx.transaction_date,
                    'transaction_id': tx.id
                })

                remaining_to_sell -= quantity_from_lot

        return total_cost, lot_details

    @staticmethod
    def calculate_hifo_cost(asset: Asset, sell_quantity: float) -> Tuple[float, List[Dict]]:
        """
        Calculate cost using HIFO method (Highest In, First Out)
        Tax optimization: sell highest cost lots first to minimize gains

        Returns:
            Tuple of (total_cost, lot_details)
        """
        transactions = AssetTransaction.query.filter_by(
            asset_id=asset.id,
            transaction_type='buy'
        ).order_by(AssetTransaction.unit_price.desc()).all()

        remaining_to_sell = sell_quantity
        total_cost = 0.0
        lot_details = []

        for tx in transactions:
            if remaining_to_sell <= 0:
                break

            if tx.quantity > 0:
                quantity_from_lot = min(tx.quantity, remaining_to_sell)
                cost_from_lot = quantity_from_lot * tx.unit_price
                total_cost += cost_from_lot

                lot_details.append({
                    'quantity': quantity_from_lot,
                    'unit_cost': tx.unit_price,
                    'total_cost': cost_from_lot,
                    'buy_date': tx.transaction_date,
                    'transaction_id': tx.id
                })

                remaining_to_sell -= quantity_from_lot

        return total_cost, lot_details

    @staticmethod
    def calculate_weighted_average_cost(asset: Asset) -> float:
        """
        Calculate weighted average cost per unit
        This is the existing method from the Asset model
        """
        transactions = AssetTransaction.query.filter_by(asset_id=asset.id).all()

        if not transactions:
            return asset.purchase_cost if asset.purchase_cost and asset.purchase_cost > 0 else asset.value

        total_quantity = 0
        total_cost = 0

        for tx in transactions:
            if tx.transaction_type == 'buy':
                total_quantity += tx.quantity
                total_cost += tx.total_cost
            elif tx.transaction_type == 'sell':
                if total_quantity > 0:
                    avg_cost = total_cost / total_quantity
                    total_quantity -= tx.quantity
                    total_cost -= (avg_cost * tx.quantity)

        if total_quantity > 0:
            return total_cost / total_quantity

        return 0.0

    @staticmethod
    def get_cost_basis(asset: Asset, cost_method: str = None) -> Dict:
        """
        Get comprehensive cost basis information for an asset

        Args:
            asset: Asset instance
            cost_method: Cost method to use (default: asset's preferred method)

        Returns:
            Dict with cost basis details
        """
        cost_method = cost_method or PortfolioAccounting.get_cost_method(asset)

        transactions = AssetTransaction.query.filter_by(asset_id=asset.id).all()

        # Calculate current position
        current_quantity = 0
        total_invested = 0

        buy_transactions = []
        for tx in transactions:
            if tx.transaction_type == 'buy':
                current_quantity += tx.quantity
                total_invested += tx.total_cost
                buy_transactions.append(tx)
            elif tx.transaction_type == 'sell':
                current_quantity -= tx.quantity

        # Calculate cost based on method
        if cost_method == CostMethod.FIFO:
            total_cost, lot_details = PortfolioAccounting.calculate_fifo_cost(asset, current_quantity)
        elif cost_method == CostMethod.LIFO:
            total_cost, lot_details = PortfolioAccounting.calculate_lifo_cost(asset, current_quantity)
        elif cost_method == CostMethod.HIFO:
            total_cost, lot_details = PortfolioAccounting.calculate_hifo_cost(asset, current_quantity)
        else:  # WEIGHTED_AVERAGE
            total_cost = PortfolioAccounting.calculate_weighted_average_cost(asset) * current_quantity
            lot_details = []

        # Tax cost (for Turkish tax purposes - simplified)
        # In Turkey, tax cost includes purchase cost + transaction fees
        tax_cost = total_cost  # Can be enhanced with fee tracking

        return {
            'cost_method': cost_method,
            'current_quantity': current_quantity,
            'total_cost': total_cost,
            'average_cost_per_unit': total_cost / current_quantity if current_quantity > 0 else 0,
            'tax_cost': tax_cost,
            'lot_details': lot_details,
            'total_invested': total_invested,
            'buy_transactions_count': len(buy_transactions)
        }

    @staticmethod
    def calculate_realized_gain(asset: Asset, sell_transaction: AssetTransaction, cost_method: str = None) -> Dict:
        """
        Calculate realized gain for a specific sale transaction

        Args:
            asset: Asset instance
            sell_transaction: The sell transaction
            cost_method: Cost method to use

        Returns:
            Dict with realized gain details
        """
        cost_method = cost_method or PortfolioAccounting.get_cost_method(asset)

        if cost_method == CostMethod.FIFO:
            cost_basis, lot_details = PortfolioAccounting.calculate_fifo_cost(asset, sell_transaction.quantity)
        elif cost_method == CostMethod.LIFO:
            cost_basis, lot_details = PortfolioAccounting.calculate_lifo_cost(asset, sell_transaction.quantity)
        elif cost_method == CostMethod.HIFO:
            cost_basis, lot_details = PortfolioAccounting.calculate_hifo_cost(asset, sell_transaction.quantity)
        else:  # WEIGHTED_AVERAGE
            avg_cost = PortfolioAccounting.calculate_weighted_average_cost(asset)
            cost_basis = avg_cost * sell_transaction.quantity
            lot_details = []

        sale_proceeds = sell_transaction.total_cost
        realized_gain = sale_proceeds - cost_basis
        gain_percentage = (realized_gain / cost_basis * 100) if cost_basis > 0 else 0

        return {
            'sale_proceeds': sale_proceeds,
            'cost_basis': cost_basis,
            'realized_gain': realized_gain,
            'gain_percentage': gain_percentage,
            'cost_method': cost_method,
            'lot_details': lot_details,
            'tax_implication': 'positive' if realized_gain > 0 else 'negative' if realized_gain < 0 else 'neutral'
        }

    @staticmethod
    def calculate_unrealized_gain(asset: Asset, cost_method: str = None) -> Dict:
        """
        Calculate unrealized gain for current position

        Args:
            asset: Asset instance
            cost_method: Cost method to use

        Returns:
            Dict with unrealized gain details
        """
        cost_basis_info = PortfolioAccounting.get_cost_basis(asset, cost_method)

        current_value = asset.value
        cost_basis = cost_basis_info['total_cost']
        unrealized_gain = current_value - cost_basis
        gain_percentage = (unrealized_gain / cost_basis * 100) if cost_basis > 0 else 0

        return {
            'current_value': current_value,
            'cost_basis': cost_basis,
            'unrealized_gain': unrealized_gain,
            'gain_percentage': gain_percentage,
            'cost_method': cost_basis_info['cost_method'],
            'current_quantity': cost_basis_info['current_quantity']
        }

    @staticmethod
    def get_portfolio_cost_summary(tenant_id: str = None) -> Dict:
        """
        Get portfolio-wide cost summary across all assets

        Args:
            tenant_id: Filter by tenant

        Returns:
            Dict with portfolio cost summary
        """
        query = Asset.query
        if tenant_id:
            query = query.filter_by(tenant_id=tenant_id)

        assets = query.all()

        summary = {
            'total_assets': len(assets),
            'total_current_value': 0,
            'total_cost_basis': 0,
            'total_realized_gain': 0,
            'total_unrealized_gain': 0,
            'by_cost_method': {},
            'asset_details': []
        }

        for asset in assets:
            cost_info = PortfolioAccounting.get_cost_basis(asset)
            unrealized_info = PortfolioAccounting.calculate_unrealized_gain(asset)

            # Calculate total realized gain from all sell transactions
            sell_transactions = AssetTransaction.query.filter_by(
                asset_id=asset.id,
                transaction_type='sell'
            ).all()

            asset_realized_gain = 0
            for sell_tx in sell_transactions:
                gain_info = PortfolioAccounting.calculate_realized_gain(asset, sell_tx)
                asset_realized_gain += gain_info['realized_gain']

            summary['total_current_value'] += asset.value
            summary['total_cost_basis'] += cost_info['total_cost']
            summary['total_unrealized_gain'] += unrealized_info['unrealized_gain']
            summary['total_realized_gain'] += asset_realized_gain

            # Group by cost method
            method = cost_info['cost_method']
            if method not in summary['by_cost_method']:
                summary['by_cost_method'][method] = {
                    'count': 0,
                    'total_value': 0,
                    'total_cost': 0
                }
            summary['by_cost_method'][method]['count'] += 1
            summary['by_cost_method'][method]['total_value'] += asset.value
            summary['by_cost_method'][method]['total_cost'] += cost_info['total_cost']

            summary['asset_details'].append({
                'asset_id': asset.id,
                'asset_name': asset.name,
                'cost_method': method,
                'current_value': asset.value,
                'cost_basis': cost_info['total_cost'],
                'unrealized_gain': unrealized_info['unrealized_gain'],
                'realized_gain': asset_realized_gain
            })

        return summary


def get_tax_cost_basis(asset: Asset, cost_method: str = None) -> Dict:
    """
    Get tax cost basis for Turkish tax reporting

    Args:
        asset: Asset instance
        cost_method: Cost method to use (default: FIFO for tax purposes in Turkey)

    Returns:
        Dict with tax-relevant cost information
    """
    # For Turkish tax purposes, FIFO is typically the default method
    cost_method = cost_method or CostMethod.FIFO

    cost_basis_info = PortfolioAccounting.get_cost_basis(asset, cost_method)

    # Tax cost includes:
    # 1. Purchase cost
    # 2. Transaction fees (can be added later)
    # 3. Other acquisition costs

    tax_cost = cost_basis_info['total_cost']

    return {
        'tax_cost': tax_cost,
        'cost_method': cost_method,
        'acquisition_date': asset.purchase_date,
        'current_quantity': cost_basis_info['current_quantity'],
        'lot_details': cost_basis_info['lot_details'],
        'tax_year': datetime.now().year
    }
