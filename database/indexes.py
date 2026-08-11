"""
Database Indexes - Index yönetimi
Performans için index oluşturma
"""

import logging

from sqlalchemy import inspect, text

from models import db

logger = logging.getLogger(__name__)


def _create_indexes_if_not_exist():
    """Performans için index oluşturur"""
    indexes = [
        ('idx_transaction_date', '"transaction"', 'date'),
        ('idx_transaction_type', '"transaction"', 'type'),
        ('idx_transaction_status', '"transaction"', 'status'),
        ('idx_transaction_type_status', '"transaction"', 'type, status'),
        ('idx_transaction_date_type', '"transaction"', 'date, type'),
        ('idx_recurring_plan_flow_type', 'recurring_plan', 'flow_type'),
        ('idx_recurring_plan_name', 'recurring_plan', 'name'),
        ('idx_asset_type', 'asset', 'type'),
        ('idx_asset_value', 'asset', 'value'),
        # MEVCUT LİSTEYE EKLE (mevcut satırları SILME):
        ('idx_transaction_tenant_id', '"transaction"', 'tenant_id'),
        ('idx_transaction_status_tenant', '"transaction"', 'status, tenant_id'),
        ('idx_transaction_date_tenant', '"transaction"', 'date, tenant_id'),
        ('idx_asset_tenant_id', 'asset', 'tenant_id'),
        ('idx_recurring_plan_tenant_id', 'recurring_plan', 'tenant_id'),
        ('idx_user_username', '"user"', 'username'),
        ('idx_user_tenant_id', '"user"', 'tenant_id'),
        ('idx_asset_update_asset_id', 'asset_update', 'asset_id'),
    ]

    inspector = inspect(db.engine)
    existing_indexes = set()

    for table_name in ['transaction', 'recurring_plan', 'asset', 'user', 'asset_update']:
        if table_name in inspector.get_table_names():
            existing_indexes.update(idx['name'] for idx in inspector.get_indexes(table_name))

    with db.engine.begin() as conn:
        for idx_name, table, columns in indexes:
            if idx_name not in existing_indexes:
                try:
                    conn.execute(text(f'CREATE INDEX IF NOT EXISTS {idx_name} ON {table} ({columns})'))
                    logger.info(f"Index oluşturuldu: {idx_name}")
                except Exception as e:
                    logger.warning(f"Index oluşturma hatası {idx_name}: {e}")
