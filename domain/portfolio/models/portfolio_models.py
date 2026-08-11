from datetime import datetime, timezone

from shared.db import db
from sqlalchemy import Numeric


def utcnow_naive():
    return datetime.now(timezone.utc).replace(tzinfo=None)


class AssetUpdate(db.Model):
    """Varlık güncelleme geçmişi modeli"""
    __tablename__ = 'asset_update'

    id = db.Column(db.Integer, primary_key=True)
    asset_id = db.Column(db.Integer, db.ForeignKey('asset.id', ondelete='CASCADE'), nullable=False)
    old_value = db.Column(Numeric(19, 4), nullable=False)
    new_value = db.Column(Numeric(19, 4), nullable=True)
    old_unit_price = db.Column(Numeric(19, 4), nullable=True)
    new_unit_price = db.Column(Numeric(19, 4), nullable=True)
    update_type = db.Column(db.String(20), nullable=False)  # 'manual', 'auto', 'bulk'
    update_source = db.Column(db.String(50), nullable=True)  # API kaynağı vb.
    notes = db.Column(db.String(200), nullable=True)
    updated_at = db.Column(db.DateTime, default=utcnow_naive)
    updated_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)

    asset = db.relationship('Asset', back_populates='updates', passive_deletes=True)
    user = db.relationship('User', backref='asset_updates')


class AssetTransaction(db.Model):
    """
    Varlık alım/satış işlemleri - Weighted Average Cost hesaplaması için
    Her alım/satım işlemi ayrı kayıt olarak tutulur
    """
    __tablename__ = 'asset_transaction'
    __table_args__ = (
        db.Index('idx_asset_transaction_asset_id', 'asset_id'),
        db.Index('idx_asset_transaction_type', 'transaction_type'),
        db.Index('idx_asset_transaction_date', 'transaction_date'),
        db.Index('idx_asset_transaction_tenant_id', 'tenant_id'),
    )

    id = db.Column(db.Integer, primary_key=True)
    asset_id = db.Column(db.Integer, db.ForeignKey('asset.id', ondelete='CASCADE'), nullable=False)
    transaction_type = db.Column(db.String(10), nullable=False)  # 'buy', 'sell'
    quantity = db.Column(Numeric(19, 4), nullable=False)  # Alınan/satılan miktar
    unit_price = db.Column(Numeric(19, 4), nullable=False)  # Birim fiyat
    total_cost = db.Column(Numeric(19, 4), nullable=False)  # Toplam maliyet (quantity * unit_price)
    transaction_date = db.Column(db.String(10), nullable=False)  # YYYY-MM-DD formatında işlem tarihi
    notes = db.Column(db.String(200), nullable=True)
    created_at = db.Column(db.DateTime, default=utcnow_naive)
    tenant_id = db.Column(db.String(50), db.ForeignKey('tenant.id'), nullable=False, index=True)

    asset = db.relationship('Asset', back_populates='transactions', passive_deletes=True)
    tenant = db.relationship('Tenant', backref='asset_transactions')


class Asset(db.Model):
    """Profesyonel Varlık modeli - Yatırım takibi için gelişmiş alanlar"""
    __tablename__ = 'asset'
    __table_args__ = (
        db.Index('idx_asset_type', 'type'),
        db.Index('idx_asset_value', 'value'),
        db.Index('idx_asset_purchase_date', 'purchase_date'),
        db.Index('idx_asset_risk_level', 'risk_level'),
        db.Index('idx_asset_tenant_id', 'tenant_id'),
    )

    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.String(50), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    value = db.Column(Numeric(19, 4), nullable=False)  # Otomatik hesaplanır: unit_price * quantity
    description = db.Column(db.String(200))

    # Profesyonel yatırım alanları
    purchase_date = db.Column(db.String(10), nullable=False)  # YYYY-MM-DD formatında satın alma tarihi
    purchase_cost = db.Column(Numeric(19, 4), nullable=False)  # Satın alma maliyeti (zorunlu)
    quantity = db.Column(Numeric(19, 4), nullable=False)  # Miktar/adet (zorunlu)
    unit_price = db.Column(Numeric(19, 4), nullable=False)  # Birim fiyat (zorunlu)
    currency = db.Column(db.String(3), nullable=False)  # Para birimi (zorunlu)
    symbol = db.Column(db.String(20), nullable=False)  # Varlık kodu (zorunlu)
    risk_level = db.Column(db.String(20), nullable=False)  # Risk seviyesi (zorunlu)
    liquidity = db.Column(db.String(20), nullable=False)  # Likidite (zorunlu)
    sector_id = db.Column(db.Integer, db.ForeignKey('asset_sector.id'), nullable=False)  # Sektör foreign key (zorunlu)
    sector = db.relationship('AssetSector', backref='assets')
    notes = db.Column(db.String(500))
    monthly_rent = db.Column(Numeric(19, 4), nullable=True)  # Aylık kira geliri (gayrimenkul için)
    is_admin_generated = db.Column(db.Boolean, default=False)
    last_updated = db.Column(db.String(10))  # Son güncelleme tarihi
    tenant_id = db.Column(db.String(50), db.ForeignKey('tenant.id'), nullable=False, index=True)
    tenant = db.relationship('Tenant', backref='assets')
    transactions = db.relationship(
        'AssetTransaction',
        back_populates='asset',
        cascade='all, delete-orphan',
        passive_deletes=True,
    )
    updates = db.relationship(
        'AssetUpdate',
        back_populates='asset',
        cascade='all, delete-orphan',
        passive_deletes=True,
    )

    # Kapatılmış (Tamamen Satılmış) Varlıklar
    is_closed = db.Column(db.Boolean, default=False, nullable=False)
    closed_at = db.Column(db.String(10), nullable=True)

    # Faz 1: Yeni Varlık Alanları
    rent_plan_id = db.Column(db.Integer, db.ForeignKey('recurring_plan.id', use_alter=True), nullable=True)
    rent_plan = db.relationship('RecurringPlan', foreign_keys=[rent_plan_id], backref='rented_assets')
    dividend_yield = db.Column(Numeric(6, 4), nullable=True)

    # Portföy Muhasebesi - Maliyet Yöntemi
    cost_method = db.Column(db.String(20), default='WEIGHTED_AVERAGE', nullable=False)  # 'FIFO', 'LIFO', 'WEIGHTED_AVERAGE', 'HIFO'

    @property
    def weighted_average_cost(self):
        """Ağırlıklı Ortalama Maliyet (WAC) hesapla"""
        from models import AssetTransaction
        from shared.decimal_precision import to_decimal

        transactions = AssetTransaction.query.filter_by(asset_id=self.id).all()

        if not transactions:
            return self.purchase_cost if self.purchase_cost and self.purchase_cost > 0 else self.value

        total_quantity = to_decimal(0)
        total_cost = to_decimal(0)

        for tx in transactions:
            qty = to_decimal(tx.quantity)
            cost = to_decimal(tx.total_cost)
            if tx.transaction_type == 'buy':
                total_quantity += qty
                total_cost += cost
            elif tx.transaction_type == 'sell':
                if total_quantity > 0:
                    avg_cost = total_cost / total_quantity
                    total_quantity -= qty
                    total_cost -= (avg_cost * qty)

        if total_quantity > 0:
            return total_cost / total_quantity

        return to_decimal(0)

    @property
    def roi(self):
        """Return on Investment hesapla - Weighted Average Cost kullanarak"""
        from shared.decimal_precision import to_decimal
        effective_cost_per_unit = to_decimal(self.weighted_average_cost)
        total_qty = to_decimal(self.quantity or 0)
        if total_qty == 0:
            from models import AssetTransaction
            txs = AssetTransaction.query.filter_by(asset_id=self.id).all()
            if txs:
                for tx in txs:
                    if tx.transaction_type == 'buy':
                        total_qty += to_decimal(tx.quantity)
                    elif tx.transaction_type == 'sell':
                        total_qty -= to_decimal(tx.quantity)

        effective_cost = effective_cost_per_unit * total_qty
        val = to_decimal(self.value or 0)

        if effective_cost > 0:
            return to_decimal(((val - effective_cost) / effective_cost) * 100)
        return to_decimal(0)


    @property
    def total_gain_loss(self):
        """Toplam getiri/kayıp = Gerçekleşmiş Kar + Gerçekleşmemiş Kar.

        Önceki hata: sadece unrealized_gain döndürülüyordu (realized_gain dahil edilmiyordu).
        Düzeltme: realized_gain + unrealized_gain toplamı döndürülür.
        Tüm ara değişkenler Decimal türünde tutulur (float karışımı önlendi).
        """
        from shared.decimal_precision import to_decimal
        try:
            r = to_decimal(self.realized_gain)
            u = to_decimal(self.unrealized_gain)
            return r + u
        except Exception:
            return to_decimal(0)

    @property
    def realized_gain(self):
        """Gerçekleşmiş kar — satış işlemlerinden elde edilen net kar/zarar.

        Önceki hata: tüm ara değişkenler float/int kullanıyordu.
        tx.quantity ve tx.total_cost SQLAlchemy'den Decimal gelir;
        float ile karıştırılması 'unsupported operand' TypeError üretiyordu.
        Düzeltme: tüm aritmetik to_decimal() ile Decimal türünde yapılır.
        """
        from models import AssetTransaction
        from shared.decimal_precision import to_decimal

        transactions = AssetTransaction.query.filter_by(asset_id=self.id).all()
        if not transactions:
            return to_decimal(0)

        realized_gain = to_decimal(0)
        avg_cost = to_decimal(0)
        total_quantity = to_decimal(0)
        total_cost = to_decimal(0)

        for tx in transactions:
            qty = to_decimal(tx.quantity)
            cost = to_decimal(tx.total_cost)
            if tx.transaction_type == 'buy':
                total_quantity += qty
                total_cost += cost
                avg_cost = total_cost / total_quantity if total_quantity > 0 else to_decimal(0)
            elif tx.transaction_type == 'sell':
                # Satış karı = satış tutarı - (miktar * ortalama maliyet)
                if avg_cost > 0:
                    gain = cost - (qty * avg_cost)
                    realized_gain += gain
                # Satış sonrası ortalama maliyet güncelle
                total_quantity -= qty
                if total_quantity > 0:
                    total_cost -= (avg_cost * qty)
                    avg_cost = total_cost / total_quantity

        return realized_gain

    @property
    def unrealized_gain(self):
        """Gerçekleşmemiş kar — mevcut pozisyonun değer artışı.

        Önceki hata: tx.quantity (Decimal) ile int 0 toplanıyordu;
        effective_cost_per_unit (Decimal) ile int/float çarpımı TypeError veriyordu.
        Düzeltme: tüm aritmetik to_decimal() ile Decimal türünde yapılır.
        """
        from models import AssetTransaction
        from shared.decimal_precision import to_decimal

        effective_cost_per_unit = to_decimal(self.weighted_average_cost)
        val = to_decimal(self.value or 0)

        transactions = AssetTransaction.query.filter_by(asset_id=self.id).all()
        if transactions:
            total_quantity = to_decimal(0)
            for tx in transactions:
                qty = to_decimal(tx.quantity)
                if tx.transaction_type == 'buy':
                    total_quantity += qty
                elif tx.transaction_type == 'sell':
                    total_quantity -= qty
            effective_cost = effective_cost_per_unit * total_quantity if total_quantity > 0 else to_decimal(0)
        else:
            qty = to_decimal(self.quantity or 0)
            effective_cost = effective_cost_per_unit * qty if qty > 0 else to_decimal(0)

        # Unrealized gain = güncel değer - kalan maliyet
        return val - effective_cost

    @property
    def portfolio_weight(self):
        """Portföy ağırlığı — sadece bu tenant'ın varlık toplamına göre hesaplanır.

        Önceki hata: get_total_assets() tenant filtresi olmadan tüm DB'yi topluyordu
        (cross-tenant veri sızıntısı). Düzeltme: Flask g'den tenant_id alınarak
        SQL seviyesinde filtreleme yapılır.
        """
        from shared.decimal_precision import to_decimal
        try:
            from flask import g
            from sqlalchemy import func
            from database.connection import db
            tenant_id = g.get('tenant_id')
            if not tenant_id:
                return to_decimal(0)
            total = db.session.query(func.sum(Asset.value)).filter(
                Asset.tenant_id == tenant_id,
                Asset.is_closed == False,
            ).scalar()
            total = to_decimal(total or 0)
            if total > 0:
                return to_decimal(self.value or 0) / total * 100
        except Exception:
            pass
        return to_decimal(0)

    @property
    def ledger_layer(self):
        return 'varlik_pozisyon'

    @property
    def origin(self):
        return 'Otomatik' if self.is_admin_generated else 'Manuel'

    @property
    def has_cash_link(self):
        from models import Transaction
        return Transaction.query.filter_by(source_id=self.id, source_type='asset').count() > 0
