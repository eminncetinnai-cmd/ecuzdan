from decimal import Decimal

import pytest

from models import Asset, AssetSector, db


@pytest.mark.regression
def test_manual_asset_roi_uses_total_purchase_cost(app):
    """Manual pozisyonlarda toplam purchase_cost quantity ile tekrar çarpılmaz."""
    with app.app_context():
        sector = AssetSector.query.first()
        if sector is None:
            sector = AssetSector(name="Test Sector")
            db.session.add(sector)
            db.session.flush()

        asset = Asset(
            type="Hisse Senedi",
            name="ROI Regression Asset",
            value=Decimal("1200.0000"),
            purchase_date="2026-01-01",
            purchase_cost=Decimal("1000.0000"),
            quantity=Decimal("10.0000"),
            unit_price=Decimal("120.0000"),
            currency="TRY",
            symbol="ROI_TEST",
            risk_level="Orta",
            liquidity="Likit",
            sector_id=sector.id,
            tenant_id="default",
            is_closed=False,
        )
        db.session.add(asset)
        db.session.commit()
        try:
            assert abs(Decimal(str(asset.roi)) - Decimal("20.0000")) < Decimal("0.0001")
            assert abs(Decimal(str(asset.unrealized_gain)) - Decimal("200.0000")) < Decimal("0.0001")
        finally:
            db.session.delete(asset)
            db.session.commit()
