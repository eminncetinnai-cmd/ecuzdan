"""Repository for portfolio asset persistence operations."""

from datetime import datetime

from models import Asset, AssetUpdate

from .base import BaseRepository
from .contracts import BaseRepositoryContract, PortfolioRepositoryContract


class PortfolioRepository(BaseRepository, BaseRepositoryContract, PortfolioRepositoryContract):
    def add_asset(
        self,
        type_,
        name,
        value,
        description,
        purchase_date=None,
        purchase_cost=0.0,
        quantity=1.0,
        unit_price=0.0,
        currency='TRY',
        symbol=None,
        risk_level='Orta',
        liquidity='Likit',
        sector_id=None,
        notes=None,
        tenant_id=None,
    ):
        asset = Asset(
            type=type_,
            name=name,
            value=value,
            description=description,
            purchase_date=purchase_date,
            purchase_cost=purchase_cost,
            quantity=quantity,
            unit_price=unit_price,
            currency=currency,
            symbol=symbol,
            risk_level=risk_level,
            liquidity=liquidity,
            sector_id=sector_id,
            notes=notes,
            last_updated=datetime.now().strftime("%Y-%m-%d"),
            tenant_id=tenant_id,
        )

        self.session.add(asset)
        self.commit()
        return asset

    def update_asset(
        self,
        asset_id,
        type_,
        name,
        value,
        description,
        purchase_date=None,
        purchase_cost=0.0,
        quantity=1.0,
        unit_price=0.0,
        currency='TRY',
        symbol=None,
        risk_level='Orta',
        liquidity='Likit',
        sector_id=None,
        notes=None,
    ):
        asset = self.db.get_or_404(Asset, asset_id)
        asset.type = type_
        asset.name = name
        asset.value = value
        asset.description = description
        asset.purchase_date = purchase_date
        asset.purchase_cost = purchase_cost
        asset.quantity = quantity
        asset.unit_price = unit_price
        asset.currency = currency
        asset.symbol = symbol
        asset.risk_level = risk_level
        asset.liquidity = liquidity
        asset.sector_id = sector_id
        asset.notes = notes

        from datetime import datetime
        asset.last_updated = datetime.now().strftime("%Y-%m-%d")

        self.commit()
        return asset

    def delete_asset(self, asset_id):
        from domain.transactions.services.financial_ledger import delete_asset_position

        return delete_asset_position(asset_id)

    def log_asset_update(
        self,
        asset_id,
        old_value,
        new_value,
        old_unit_price=None,
        new_unit_price=None,
        update_type='manual',
        update_source=None,
        notes=None,
        user_id=None,
        auto_commit=True,
    ):
        update = AssetUpdate(
            asset_id=asset_id,
            old_value=old_value,
            new_value=new_value,
            old_unit_price=old_unit_price,
            new_unit_price=new_unit_price,
            update_type=update_type,
            update_source=update_source,
            notes=notes,
            updated_by=user_id,
        )
        self.session.add(update)
        if auto_commit:
            self.commit()
        return update

    def get_asset_update_history(self, asset_id, limit=50):
        return self.query(AssetUpdate).filter_by(asset_id=asset_id).order_by(AssetUpdate.updated_at.desc()).limit(limit).all()

    def bulk_update_assets(self, asset_ids, new_unit_prices, user_id=None, notes=None):
        updated_assets = []
        for asset_id, new_unit_price in zip(asset_ids, new_unit_prices):
            asset = self.db.session.get(Asset, asset_id)
            if asset:
                old_value = asset.value
                old_unit_price = asset.unit_price
                asset.unit_price = new_unit_price
                asset.value = new_unit_price * asset.quantity

                update = AssetUpdate(
                    asset_id=asset.id,
                    old_value=old_value,
                    new_value=asset.value,
                    old_unit_price=old_unit_price,
                    new_unit_price=new_unit_price,
                    update_type='bulk',
                    notes=notes,
                    updated_by=user_id,
                )
                self.session.add(update)
                updated_assets.append(asset)

        self.db.session.commit()
        return updated_assets
