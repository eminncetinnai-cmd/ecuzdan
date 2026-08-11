"""
Multi-Currency Service
=======================
Base currency logic and currency conversion for accurate portfolio valuation
Phase 5: Multi-currency base currency logic
"""

import logging
from typing import Dict

from models import Asset, Transaction, User, db

logger = logging.getLogger(__name__)


class CurrencyManager:
    """Multi-currency management with base currency logic"""

    # Supported currencies
    SUPPORTED_CURRENCIES = {
        'TRY': {'name': 'Türk Lirası', 'symbol': '₺', 'base_for': ['TR']},
        'USD': {'name': 'US Dollar', 'symbol': '$', 'base_for': ['US']},
        'EUR': {'name': 'Euro', 'symbol': '€', 'base_for': ['EU']},
        'GBP': {'name': 'British Pound', 'symbol': '£', 'base_for': ['GB']},
        'XAU': {'name': 'Gold (Gram)', 'symbol': 'gr', 'base_for': ['XAU']},
        'XAG': {'name': 'Silver (Gram)', 'symbol': 'gr', 'base_for': ['XAG']},
        'BTC': {'name': 'Bitcoin', 'symbol': '₿', 'base_for': ['BTC']},
        'ETH': {'name': 'Ethereum', 'symbol': 'Ξ', 'base_for': ['ETH']},
    }

    @staticmethod
    def get_base_currency(tenant_id: str = None, user_id: int = None) -> str:
        """
        Get base currency for tenant or user

        Args:
            tenant_id: Tenant ID
            user_id: User ID (overrides tenant setting)

        Returns:
            Base currency code (e.g., 'TRY')
        """
        # Check user-specific setting first. base_currency nullable'dır:
        # dolu değilse kullanıcının tenant'ına düşülür, None döndürülmez.
        if user_id:
            user = db.session.get(User, user_id)
            if user:
                if user.base_currency:
                    return user.base_currency
                if not tenant_id:
                    tenant_id = user.tenant_id

        # Check tenant setting
        if tenant_id:
            from models import Tenant
            tenant = db.session.get(Tenant, tenant_id)
            if tenant and tenant.base_currency:
                return tenant.base_currency

        # Default to TRY for Turkish users
        return 'TRY'

    @staticmethod
    def set_base_currency(tenant_id: str = None, user_id: int = None, currency: str = 'TRY') -> bool:
        """
        Set base currency for tenant or user

        Args:
            tenant_id: Tenant ID
            user_id: User ID
            currency: Currency code

        Returns:
            Success status
        """
        if currency not in CurrencyManager.SUPPORTED_CURRENCIES:
            logger.error(f"Unsupported currency: {currency}")
            return False

        if user_id:
            user = db.session.get(User, user_id)
            if user:
                if not hasattr(user, 'base_currency'):
                    # Add base_currency field if not exists (migration needed)
                    logger.warning("User model needs base_currency field migration")
                    return False
                user.base_currency = currency
                db.session.commit()
                logger.info(f"Set base currency for user {user_id}: {currency}")
                return True

        if tenant_id:
            from models import Tenant
            tenant = db.session.get(Tenant, tenant_id)
            if tenant:
                if not hasattr(tenant, 'base_currency'):
                    logger.warning("Tenant model needs base_currency field migration")
                    return False
                tenant.base_currency = currency
                db.session.commit()
                logger.info(f"Set base currency for tenant {tenant_id}: {currency}")
                return True

        return False

    @staticmethod
    def get_exchange_rate(from_currency: str, to_currency: str, date: str = None) -> float:
        """
        Get exchange rate between currencies

        Args:
            from_currency: Source currency
            to_currency: Target currency
            date: Date for historical rate (YYYY-MM-DD)

        Returns:
            Exchange rate (1 unit of from_currency = X units of to_currency)
        """
        if from_currency == to_currency:
            return 1.0

        # Try to get from market data service
        try:
            from market_data_service import get_exchange_rate
            rate = get_exchange_rate(from_currency, to_currency, date)
            if rate and rate > 0:
                return rate
        except Exception as e:
            logger.warning(f"Failed to get exchange rate from market service: {e}")

        # Fallback to hardcoded rates (for testing/backup)
        fallback_rates = {
            ('USD', 'TRY'): 32.0,
            ('EUR', 'TRY'): 35.0,
            ('GBP', 'TRY'): 40.0,
            ('XAU', 'TRY'): 2400.0,  # Gold per gram
            ('XAG', 'TRY'): 30.0,   # Silver per gram
            ('BTC', 'TRY'): 3200000.0,
            ('ETH', 'TRY'): 120000.0,
            ('TRY', 'USD'): 1/32.0,
            ('TRY', 'EUR'): 1/35.0,
            ('TRY', 'GBP'): 1/40.0,
        }

        rate = fallback_rates.get((from_currency, to_currency))
        if rate:
            logger.info(f"Using fallback rate for {from_currency}/{to_currency}: {rate}")
            return rate

        # Try inverse
        inverse_rate = fallback_rates.get((to_currency, from_currency))
        if inverse_rate:
            return 1.0 / inverse_rate

        logger.error(f"No exchange rate available for {from_currency}/{to_currency}")
        return 1.0

    @staticmethod
    def convert_currency(amount: float, from_currency: str, to_currency: str, date: str = None) -> float:
        """
        Convert amount from one currency to another

        Args:
            amount: Amount to convert
            from_currency: Source currency
            to_currency: Target currency
            date: Date for historical rate

        Returns:
            Converted amount
        """
        if from_currency == to_currency:
            return amount

        rate = CurrencyManager.get_exchange_rate(from_currency, to_currency, date)
        return amount * rate

    @staticmethod
    def get_asset_value_in_base_currency(asset: Asset, base_currency: str = None) -> Dict:
        """
        Get asset value converted to base currency

        Args:
            asset: Asset instance
            base_currency: Target currency (default: tenant base currency)

        Returns:
            Dict with multi-currency valuation
        """
        if not base_currency:
            base_currency = CurrencyManager.get_base_currency(asset.tenant_id)

        asset_currency = asset.currency
        current_value = asset.value

        # Convert to base currency
        base_value = CurrencyManager.convert_currency(
            current_value,
            asset_currency,
            base_currency
        )

        # Also provide values in major currencies
        major_currencies = ['TRY', 'USD', 'EUR']
        currency_values = {}

        for currency in major_currencies:
            if currency != asset_currency:
                currency_values[currency] = CurrencyManager.convert_currency(
                    current_value,
                    asset_currency,
                    currency
                )
            else:
                currency_values[currency] = current_value

        return {
            'asset_currency': asset_currency,
            'asset_value': current_value,
            'base_currency': base_currency,
            'base_value': base_value,
            'currency_values': currency_values,
            'exchange_rate_used': CurrencyManager.get_exchange_rate(asset_currency, base_currency)
        }

    @staticmethod
    def get_portfolio_multi_currency_summary(tenant_id: str = None) -> Dict:
        """
        Get portfolio summary with multi-currency breakdown

        Args:
            tenant_id: Filter by tenant

        Returns:
            Dict with multi-currency portfolio analysis
        """
        query = Asset.query
        if tenant_id:
            query = query.filter_by(tenant_id=tenant_id)

        assets = query.all()

        if not assets:
            return {
                'total_assets': 0,
                'base_currency': 'TRY',
                'total_base_value': 0,
                'by_currency': {},
                'currency_exposure': {}
            }

        base_currency = CurrencyManager.get_base_currency(tenant_id)

        # Group by currency
        by_currency = {}
        total_base_value = 0

        for asset in assets:
            asset_currency = asset.currency

            if asset_currency not in by_currency:
                by_currency[asset_currency] = {
                    'count': 0,
                    'total_value': 0,
                    'base_value': 0,
                    'assets': []
                }

            by_currency[asset_currency]['count'] += 1
            by_currency[asset_currency]['total_value'] += asset.value

            # Convert to base currency
            base_value = CurrencyManager.convert_currency(
                asset.value,
                asset_currency,
                base_currency
            )

            by_currency[asset_currency]['base_value'] += base_value
            total_base_value += base_value

            by_currency[asset_currency]['assets'].append({
                'id': asset.id,
                'name': asset.name,
                'value': asset.value,
                'base_value': base_value
            })

        # Calculate currency exposure (percentage)
        currency_exposure = {}
        for currency, data in by_currency.items():
            exposure = (data['base_value'] / total_base_value * 100) if total_base_value > 0 else 0
            currency_exposure[currency] = exposure

        return {
            'total_assets': len(assets),
            'base_currency': base_currency,
            'total_base_value': total_base_value,
            'by_currency': by_currency,
            'currency_exposure': currency_exposure,
            'currency_risk': CurrencyManager._assess_currency_risk(currency_exposure)
        }

    @staticmethod
    def _assess_currency_risk(exposure: Dict[str, float]) -> Dict:
        """
        Assess currency concentration risk

        Args:
            exposure: Currency exposure percentages

        Returns:
            Risk assessment
        """
        risk_level = 'Düşük'
        warnings = []

        # Check if any currency exceeds 50%
        for currency, pct in exposure.items():
            if pct > 50:
                risk_level = 'Yüksek'
                warnings.append(f"{currency} exposure > 50%: {pct:.1f}%")
            elif pct > 30:
                if risk_level != 'Yüksek':
                    risk_level = 'Orta'
                warnings.append(f"{currency} exposure > 30%: {pct:.1f}%")

        # Check base currency dominance
        base_currencies = ['TRY', 'USD', 'EUR']
        base_exposure = sum(exposure.get(curr, 0) for curr in base_currencies)

        if base_exposure < 50:
            warnings.append(f"Major currency exposure low: {base_exposure:.1f}%")
            if risk_level != 'Yüksek':
                risk_level = 'Orta'

        return {
            'level': risk_level,
            'warnings': warnings,
            'diversification_score': min(100, len(exposure) * 20)  # Simple score
        }

    @staticmethod
    def get_transaction_value_in_base_currency(transaction: Transaction, base_currency: str = None) -> Dict:
        """
        Get transaction value in base currency

        Args:
            transaction: Transaction instance
            base_currency: Target currency

        Returns:
            Dict with multi-currency transaction value
        """
        if not base_currency:
            base_currency = CurrencyManager.get_base_currency(transaction.tenant_id)

        # For transactions, assume they're in base currency unless specified
        # In a full implementation, transactions would have currency fields
        tx_currency = getattr(transaction, 'currency', base_currency)
        tx_amount = transaction.amount

        base_amount = CurrencyManager.convert_currency(
            tx_amount,
            tx_currency,
            base_currency
        )

        return {
            'transaction_currency': tx_currency,
            'transaction_amount': tx_amount,
            'base_currency': base_currency,
            'base_amount': base_amount,
            'exchange_rate': CurrencyManager.get_exchange_rate(tx_currency, base_currency)
        }
