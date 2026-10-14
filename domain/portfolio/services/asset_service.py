"""Asset page orchestration service."""

from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from domain.transactions.services.financial_ledger import get_asset_ledger_summaries
from engines.financial_engine import get_asset_analysis
from shared.decimal_precision import to_decimal

if TYPE_CHECKING:
    pass

class AssetService:
    def __init__(self, financial_repository=None, catalog_repository=None):
        self.financial_repository = financial_repository
        self.catalog_repository = catalog_repository

    def assets_view_context(self, tenant_id=None):
        assets = self.financial_repository.list_assets(tenant_id)
        types = self.catalog_repository.list_asset_types()
        sectors = self.catalog_repository.list_asset_sectors()
        ledger_summaries = get_asset_ledger_summaries([a.id for a in assets], tenant_id)
        analysis = self._analysis_or_fallback(assets, tenant_id)

        labels, values = [], []
        total_portfolio = to_decimal(0)
        for asset_type in types:
            subtotal = sum((to_decimal(getattr(a, 'value', 0)) for a in assets if a.type == asset_type.name), to_decimal(0))
            if subtotal > to_decimal(0):
                total_portfolio += subtotal
                labels.append(asset_type.name)
                values.append(str(subtotal.quantize(Decimal('1.00'))))
        sorted_assets = sorted(assets, key=lambda item: item.value, reverse=True)[:10]
        return {
            'assets': assets,
            'ledger_summaries': ledger_summaries,
            'total_portfolio': str(total_portfolio.quantize(Decimal('1.00'))),
            'type_labels': labels,
            'type_values': values,
            'asset_labels': [a.name for a in sorted_assets],
            'analysis': analysis,
            'asset_types': types,
            'asset_sectors': sectors,
        }

    def management_context(self, page=1, edit_id=None, tenant_id=None, per_page=20):
        edit_asset = self.financial_repository.get_asset_for_tenant(edit_id, tenant_id) if edit_id else None
        return {
            'assets_page': self.financial_repository.asset_page(page=page, per_page=per_page, tenant_id=tenant_id),
            'asset_types': self.catalog_repository.list_asset_types(),
            'asset_sectors': self.catalog_repository.list_asset_sectors(),
            'edit_id': edit_id,
            'edit_asset_data': self._edit_asset_data(edit_asset),
        }

    def unified_context(self, tenant_id=None):
        assets = self.financial_repository.list_assets(tenant_id)
        types = self.catalog_repository.list_asset_types()
        sectors = self.catalog_repository.list_asset_sectors()
        analysis = self._analysis_or_fallback(assets, tenant_id)
        ledger_summaries = get_asset_ledger_summaries([a.id for a in assets], tenant_id)

        return {
            'assets': assets,
            'analysis': analysis,
            'asset_types': types,
            'asset_sectors': sectors,
            'ledger_summaries': ledger_summaries,
        }

    def portfolio_snapshot_context(self, tenant_id=None):
        """Return a tenant-scoped, persisted-value portfolio snapshot.

        This is intentionally lighter than the full assets-view analysis. It
        does not call market providers, calculate FX, or consolidate values
        across currencies. The workspace must never present persisted manual
        valuations as live market marks.
        """
        assets = self.financial_repository.list_assets(tenant_id)
        open_assets = [asset for asset in assets if not getattr(asset, 'is_closed', False)]
        currency_totals = {}
        valuation_dates = []

        for asset in open_assets:
            currency = str(getattr(asset, 'currency', None) or 'TRY').upper()
            value = to_decimal(getattr(asset, 'value', 0) or 0)
            currency_totals[currency] = currency_totals.get(currency, to_decimal(0)) + value
            last_updated = getattr(asset, 'last_updated', None)
            if last_updated:
                valuation_dates.append(str(last_updated))

        return {
            'asset_count': len(open_assets),
            'closed_asset_count': len(assets) - len(open_assets),
            'currency_count': len(currency_totals),
            'currency_totals': {
                currency: str(value.quantize(Decimal('1.00')))
                for currency, value in sorted(currency_totals.items())
            },
            'last_valuation_date': max(valuation_dates, default=None),
            'valuation_basis': 'persisted_asset_value',
            'market_marked': False,
        }

    def _analysis_or_fallback(self, assets, tenant_id):

        import logging

        from shared.decimal_precision import to_decimal
        logger = logging.getLogger(__name__)
        try:
            analysis = get_asset_analysis(tenant_id)
            # sum() bos liste icin int 0 dondurur; Decimal + int = TypeError.
            # Duzeltme: baslangic degeri olarak to_decimal(0) kullanilir.
            analysis['total_realized_gain'] = sum((to_decimal(getattr(a, 'realized_gain', 0)) for a in assets), to_decimal(0))
            analysis['total_unrealized_gain'] = sum((to_decimal(getattr(a, 'unrealized_gain', 0)) for a in assets), to_decimal(0))
            return analysis
        except Exception as e:
            logger.error(f"Analysis fallback error: {e}")
            total_value = sum((to_decimal(a.value or 0) for a in assets), to_decimal(0))
            total_cost = sum((to_decimal(a.purchase_cost or 0) for a in assets), to_decimal(0))
            total_realized = sum((to_decimal(getattr(a, 'realized_gain', 0)) for a in assets), to_decimal(0))
            total_unrealized = sum((to_decimal(getattr(a, 'unrealized_gain', 0)) for a in assets), to_decimal(0))
            return {
                'total_value': total_value,
                'total_cost': total_cost,
                'total_gain_loss': total_realized + total_unrealized,
                'overall_roi': 0,
                'asset_count': len(assets),
                'by_type': {},
                'by_risk': {},
                'by_liquidity': {},
                'by_sector': {},
                'top_performers': [],
                'worst_performers': [],
                'portfolio_concentration': {},
                'risk_score': 0,
                'liquidity_score': 0,
                'total_realized_gain': total_realized,
                'total_unrealized_gain': total_unrealized,
            }

    def _edit_asset_data(self, asset):
        if not asset:
            return None
        purchase_date = ''
        if asset.purchase_date:
            try:
                purchase_date = datetime.strptime(asset.purchase_date, '%Y-%m-%d').strftime('%d/%m/%Y')
            except ValueError:
                purchase_date = asset.purchase_date
        return {
            'id': asset.id,
            'type': asset.type or '',
            'name': asset.name or '',
            'symbol': asset.symbol or '',
            'currency': asset.currency or 'TRY',
            'description': asset.description or '',
            'quantity': str(to_decimal(asset.quantity or 1)),
            'unit_price': str(to_decimal(asset.unit_price or 0)),
            'value': str(to_decimal(asset.value or 0)),
            'purchase_date': purchase_date,
            'purchase_cost': str(to_decimal(asset.purchase_cost or 0)),
            'risk_level': asset.risk_level or 'Orta',
            'liquidity': asset.liquidity or 'Likit',
            'sector_id': asset.sector_id,
            'notes': asset.notes or '',
            'is_closed': asset.is_closed,
        }

