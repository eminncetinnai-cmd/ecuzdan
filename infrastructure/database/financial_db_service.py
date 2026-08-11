"""
Database service layer for financial data retrieval.
Separates database access logic from financial engine to avoid circular imports.
"""

import logging

from flask import g, has_request_context

from models import Asset, RecurringPlan, Transaction

logger = logging.getLogger(__name__)


def _resolve_tenant_id(tenant_id=None):
    if tenant_id:
        return tenant_id
    if has_request_context():
        return g.get('tenant_id')
    return None


def get_actual_cash(tenant_id=None):
    """
    Ödenmiş işlemlere göre güncel nakit miktarını hesaplar

    Returns:
        float: Toplam nakit miktarı
    """
    tenant_id = _resolve_tenant_id(tenant_id)
    query = Transaction.query
    if tenant_id:
        query = query.filter_by(tenant_id=tenant_id)
    transactions = query.all()
    return sum(t.amount if t.type == 'Gelir' else -t.amount for t in transactions if t.status == 'Ödendi')


def get_total_assets(tenant_id=None):
    """
    Toplam varlık değerini hesaplar

    Returns:
        float: Toplam varlık değeri
    """
    tenant_id = _resolve_tenant_id(tenant_id)
    query = Asset.query
    if tenant_id:
        query = query.filter_by(tenant_id=tenant_id)
    assets = query.all()
    return sum(a.value for a in assets)


def get_total_debts(tenant_id=None):
    """
    Toplam borç miktarını hesaplar (düzenli gider planları)

    Returns:
        float: Toplam borç miktarı
    """
    tenant_id = _resolve_tenant_id(tenant_id)
    query = RecurringPlan.query.filter_by(flow_type='Gider')
    if tenant_id:
        query = query.filter_by(tenant_id=tenant_id)
    plans = query.all()
    return sum(p.amount * p.installments for p in plans)
