"""Factory for creating demo assets."""

import random
from datetime import datetime
from decimal import Decimal
from typing import Dict, Any, Optional

from domain.categories.services.category_service import CategoryService
from domain.demo.config_loader import DemoDataConfigLoader
from models import Asset, AssetSector
from shared.decimal_precision import to_decimal


class AssetFactory:
    """Factory for creating demo assets with category validation."""

    def __init__(self, tenant_id: Optional[str] = None):
        """
        Initialize the asset factory.
        
        Args:
            tenant_id: Tenant ID for tenant-scoped operations
        """
        self.tenant_id = tenant_id
        self.category_service = CategoryService()
        self.config_loader = DemoDataConfigLoader()

    def create_asset(
        self,
        asset_type: str,
        name: str,
        symbol: Optional[str],
        value: float,
        purchase_date: str,
        purchase_cost: float,
        quantity: float,
        unit_price: float,
        currency: str,
        risk_level: str,
        liquidity: str,
        sector_id: Optional[int],
        description: Optional[str] = None,
        notes: Optional[str] = None,
        is_admin_generated: bool = False
    ) -> Optional[Asset]:
        """
        Create an asset with category validation.
        
        Args:
            asset_type: Asset type (e.g., 'Hisse Senedi', 'Altın')
            name: Asset name
            symbol: Asset symbol (optional)
            value: Current value
            purchase_date: Purchase date (YYYY-MM-DD format)
            purchase_cost: Purchase cost
            quantity: Quantity
            unit_price: Unit price
            currency: Currency code
            risk_level: Risk level
            liquidity: Liquidity
            sector_id: Sector ID (optional)
            description: Description (optional)
            notes: Notes (optional)
            is_admin_generated: Whether this is admin-generated data
        
        Returns:
            Asset object or None if category is invalid
        """
        # Validate asset category exists
        if not self.category_service.is_valid_category(asset_type, self.tenant_id):
            return None
        
        # Create asset
        asset = Asset(
            type=asset_type,
            name=name,
            symbol=symbol,
            value=to_decimal(value),
            purchase_date=purchase_date,
            purchase_cost=to_decimal(purchase_cost),
            quantity=to_decimal(quantity),
            unit_price=to_decimal(unit_price),
            currency=currency,
            risk_level=risk_level,
            liquidity=liquidity,
            sector_id=sector_id,
            description=description,
            notes=notes,
            is_admin_generated=is_admin_generated,
            tenant_id=self.tenant_id
        )
        
        return asset

    def create_asset_from_template(
        self,
        template_name: str,
        name: str,
        symbol: str,
        purchase_date: str,
        variation_percent: float = 0.0,
        is_admin_generated: bool = False
    ) -> Optional[Asset]:
        """
        Create an asset from a predefined template.
        
        Args:
            template_name: Template name (e.g., 'stock', 'gold')
            name: Asset name
            symbol: Asset symbol
            purchase_date: Purchase date (YYYY-MM-DD format)
            variation_percent: Amount variation percentage
            is_admin_generated: Whether this is admin-generated data
        
        Returns:
            Asset object or None if template/invalid
        """
        template = self.config_loader.get_asset_template(template_name)
        if not template:
            return None
        
        # Calculate quantity and price with variation
        base_quantity = template.get('base_quantity', 1)
        quantity_range = template.get('quantity_range', {})
        if quantity_range:
            quantity = random.uniform(quantity_range['min'], quantity_range['max'])
        else:
            quantity = base_quantity * (1 + random.uniform(-variation_percent, variation_percent))
        
        base_price = template.get('base_price', 0)
        price_range = template.get('price_range', {})
        if price_range:
            unit_price = random.uniform(price_range['min'], price_range['max'])
        else:
            unit_price = base_price * (1 + random.uniform(-variation_percent, variation_percent))
        
        purchase_cost = quantity * unit_price
        value = purchase_cost
        
        return self.create_asset(
            asset_type=template.get('type'),
            name=name,
            symbol=symbol,
            value=value,
            purchase_date=purchase_date,
            purchase_cost=purchase_cost,
            quantity=quantity,
            unit_price=unit_price,
            currency=template.get('currency', 'TRY'),
            risk_level=template.get('risk_level', 'Orta'),
            liquidity=template.get('liquidity', 'Likit'),
            sector_id=None,  # Sector will be set by caller
            description=f"[Demo] {name}",
            notes="Demo data",
            is_admin_generated=is_admin_generated
        )

    def get_or_create_sector(self, sector_name: str) -> AssetSector:
        """
        Get or create an asset sector.
        
        Args:
            sector_name: Sector name
        
        Returns:
            AssetSector object
        """
        sector = AssetSector.query.filter_by(name=sector_name).first()
        if not sector:
            sector = AssetSector(name=sector_name)
            from models import db
            db.session.add(sector)
            db.session.flush()
        return sector

    def create_asset_valuation(
        self,
        asset_id: int,
        old_value: float,
        new_value: float,
        old_unit_price: float,
        new_unit_price: float,
        update_type: str = 'manual',
        notes: Optional[str] = None,
        updated_at: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create asset valuation data (not the model, just the data).
        
        Args:
            asset_id: Asset ID
            old_value: Old value
            new_value: New value
            old_unit_price: Old unit price
            new_unit_price: New unit price
            update_type: Update type
            notes: Notes
            updated_at: Update date (YYYY-MM-DD format)
        
        Returns:
            Dictionary with valuation data
        """
        if updated_at is None:
            updated_at = datetime.now().strftime('%Y-%m-%d')
        
        return {
            'asset_id': asset_id,
            'old_value': to_decimal(old_value),
            'new_value': to_decimal(new_value),
            'old_unit_price': to_decimal(old_unit_price),
            'new_unit_price': to_decimal(new_unit_price),
            'update_type': update_type,
            'notes': notes,
            'updated_at': datetime.strptime(updated_at, '%Y-%m-%d')
        }
