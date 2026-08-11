"""
Database Module - Veritabanı işlemleri
Bu modül veritabanı bağlantı, migration, CRUD işlemleri, seeding ve index yönetimini içerir.
"""

# Ana init_database fonksiyonu
from .connection import init_database

# CRUD işlemleri
from .crud import (
    add_asset,
    add_transaction,
    bulk_update_assets,
    delete_asset,
    delete_asset_sector,
    delete_asset_type,
    delete_category,
    delete_transaction,
    get_actual_cash,
    get_asset_update_history,
    get_calendar_month_data,
    get_monthly_balance,
    get_pending_payments,
    get_total_assets,
    get_total_debts,
    get_transactions_by_date_range,
    log_asset_update,
    update_asset,
    update_asset_sector,
    update_asset_type,
    update_category,
    update_transaction,
)

__all__ = [
    'init_database',
    # CRUD operations
    'get_monthly_balance',
    'get_actual_cash',
    'get_total_assets',
    'get_total_debts',
    'get_transactions_by_date_range',
    'get_calendar_month_data',
    'get_pending_payments',
    'add_transaction',
    'update_transaction',
    'delete_transaction',
    'add_asset',
    'update_asset',
    'delete_asset',
    'log_asset_update',
    'get_asset_update_history',
    'bulk_update_assets',
    'update_category',
    'delete_category',
    'update_asset_type',
    'delete_asset_type',
    'update_asset_sector',
    'delete_asset_sector',
]
