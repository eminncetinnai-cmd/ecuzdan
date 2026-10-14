"""Asset ledger summary and valuation query service."""

from domain.transactions.constants import (
    SOURCE_TYPE_ASSET,
    SOURCE_TYPE_PLAN,
    TRANSACTION_STATUS_PAID,
    TRANSACTION_STATUS_PENDING,
    TRANSACTION_TYPE_EXPENSE,
    TRANSACTION_TYPE_INCOME,
)
from models import Asset, AssetUpdate, Transaction, db
from shared.decimal_precision import to_decimal

from .helpers import _resolve_tenant_id


def get_asset_ledger_summary(asset_id, tenant_id=None):
    """Varlık için defter özeti: değerleme sayısı ve nakit bağlantısı."""
    tenant_id = _resolve_tenant_id(tenant_id)

    query = Asset.query
    if tenant_id:
        query = query.filter_by(tenant_id=tenant_id)
    asset = query.filter(Asset.id == asset_id).first()
    if not asset:
        return None
    updates = AssetUpdate.query.filter_by(asset_id=asset_id).count()
    cash_link = Transaction.query.filter_by(source_id=asset_id, source_type=SOURCE_TYPE_ASSET).first()
    return {
        'asset': asset,
        'valuation_count': updates,
        'has_cash_link': cash_link is not None,
        'cash_amount': cash_link.amount if cash_link else 0,
    }


def get_asset_ledger_summaries(asset_ids, tenant_id=None):
    """Çoklu varlık için defter özetleri (N+1 problemi çözümü)."""
    tenant_id = _resolve_tenant_id(tenant_id)

    if not asset_ids:
        return {}

    # Tüm varlıkları tek sorguda getir
    query = Asset.query.filter(Asset.id.in_(asset_ids))
    if tenant_id:
        query = query.filter_by(tenant_id=tenant_id)
    assets = {a.id: a for a in query.all()}

    # Tüm değerleme sayılarını tek sorguda getir
    update_counts = {}
    if assets:
        from sqlalchemy import func
        counts = db.session.query(
            AssetUpdate.asset_id,
            func.count(AssetUpdate.id)
        ).filter(
            AssetUpdate.asset_id.in_(asset_ids)
        ).group_by(AssetUpdate.asset_id).all()
        update_counts = {asset_id: count for asset_id, count in counts}

    # Tüm nakit bağlantılarını tek sorguda getir
    cash_links = {}
    if assets:
        links = Transaction.query.filter(
            Transaction.source_id.in_(asset_ids),
            Transaction.source_type == SOURCE_TYPE_ASSET
        ).all()
        cash_links = {link.source_id: link for link in links}

    # Sonuçları birleştir
    summaries = {}
    for asset_id in asset_ids:
        asset = assets.get(asset_id)
        if not asset:
            summaries[asset_id] = None
            continue

        summaries[asset_id] = {
            'asset': asset,
            'valuation_count': update_counts.get(asset_id, 0),
            'has_cash_link': asset_id in cash_links,
            'cash_amount': cash_links[asset_id].amount if asset_id in cash_links else 0,
        }

    return summaries


def calculate_transaction_batch_summary(tx_items) -> dict:
    """İşlem listesi için toplam, ödenen, bekleyen ve net tutar özetini hesaplar."""
    paid_income_total = to_decimal(0)
    paid_expense_total = to_decimal(0)
    pending_income_total = to_decimal(0)
    pending_expense_total = to_decimal(0)
    paid_count = 0
    pending_count = 0
    plan_count = 0

    items_list = list(tx_items) if tx_items else []

    for t in items_list:
        t_status = getattr(t, 'status', None)
        t_type = getattr(t, 'type', None)
        dec_amt = to_decimal(getattr(t, 'amount', 0) or 0)

        if t_status == TRANSACTION_STATUS_PAID:
            paid_count += 1
            if t_type == TRANSACTION_TYPE_INCOME:
                paid_income_total += dec_amt
            elif t_type == TRANSACTION_TYPE_EXPENSE:
                paid_expense_total += dec_amt
        elif t_status == TRANSACTION_STATUS_PENDING:
            pending_count += 1
            if t_type == TRANSACTION_TYPE_EXPENSE:
                pending_expense_total += dec_amt
            elif t_type == TRANSACTION_TYPE_INCOME:
                pending_income_total += dec_amt

        if getattr(t, 'source_type', None) == SOURCE_TYPE_PLAN:
            plan_count += 1

    paid_net_total = paid_income_total - paid_expense_total

    return {
        'total_count': len(items_list),
        'paid_count': paid_count,
        'pending_count': pending_count,
        'plan_count': plan_count,
        'paid_income_total': paid_income_total,
        'paid_expense_total': paid_expense_total,
        'paid_net_total': paid_net_total,
        'pending_expense_total': pending_expense_total,
        'pending_income_total': pending_income_total,
    }
