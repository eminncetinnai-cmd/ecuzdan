"""
Database Indexes - Index yönetimi
Performans için index oluşturma ve mükerrer indekslerin temizlenmesi
"""

import logging

from sqlalchemy import inspect, text

from models import db

logger = logging.getLogger(__name__)


def _create_indexes_if_not_exist():
    """Performans için kritik indeksleri oluşturur ve mükerrer indeksleri temizler."""
    ctx = None
    try:
        from flask import has_app_context
        if not has_app_context():
            from app import app
            ctx = app.app_context()
    except Exception:
        ctx = None

    def _do_index_sync():
        indexes = [
            # Transaction temel indeksleri
            ('idx_transaction_date', '"transaction"', 'date'),
            ('idx_transaction_type', '"transaction"', 'type'),
            ('idx_transaction_status', '"transaction"', 'status'),
            ('idx_transaction_type_status', '"transaction"', 'type, status'),
            ('idx_transaction_date_type', '"transaction"', 'date, type'),
            # Transaction kritik kompozit indeksleri (Nakit akışı, mutabakat, varlık silme hızlandırma)
            ('idx_transaction_source', '"transaction"', 'source_id, source_type'),
            ('idx_transaction_tenant_date', '"transaction"', 'tenant_id, date'),
            ('idx_transaction_tenant_del_date', '"transaction"', 'tenant_id, is_deleted, date'),
            ('idx_transaction_tenant_status', '"transaction"', 'tenant_id, status'),
            # Recurring plan indeksleri
            ('idx_recurring_plan_flow_type', 'recurring_plan', 'flow_type'),
            ('idx_recurring_plan_name', 'recurring_plan', 'name'),
            # Asset indeksleri
            ('idx_asset_type', 'asset', 'type'),
            ('idx_asset_value', 'asset', 'value'),
            ('idx_asset_last_updated', 'asset', 'last_updated'),
            ('idx_asset_update_asset_id', 'asset_update', 'asset_id'),
            # Bildirim ve kullanıcı
            ('idx_notification_user_read_created', 'notification', 'user_id, is_read, created_at'),
            ('idx_quiz_attempt_user_completed', 'quiz_attempt', 'user_id, completed_at'),
            # Defter & Mutabakat indeksleri
            ('idx_account_tenant_name', 'account', 'tenant_id, name'),
            ('idx_ll_journal', 'ledger_line', 'journal_entry_id'),
            ('idx_ll_account', 'ledger_line', 'account_id'),
            ('idx_je_tenant_date', 'journal_entry', 'tenant_id, date'),
            ('idx_ledger_adjustment_orig', 'ledger_adjustment', 'original_transaction_id'),
            ('idx_ledger_audit_tx', 'ledger_audit_event', 'transaction_id'),
            ('idx_plan_occurrence_plan_status', 'plan_occurrence', 'plan_id, status'),
            ('idx_payment_plan', 'payment', 'plan_id, installment_number'),
        ]

        target_tables = [
            'transaction', 'recurring_plan', 'asset', 'user', 'asset_update',
            'account', 'ledger_line', 'journal_entry',
            'ledger_adjustment', 'ledger_audit_event', 'plan_occurrence', 'payment',
            'notification', 'quiz_attempt'
        ]

        inspector = inspect(db.engine)
        available_tables = set(inspector.get_table_names())

        existing_indexes = set()
        for table_name in target_tables:
            if table_name in available_tables:
                existing_indexes.update(idx['name'] for idx in inspector.get_indexes(table_name))

        with db.engine.begin() as conn:
            for idx_name, table, columns in indexes:
                raw_table = table.strip('"').strip("'")
                if raw_table not in available_tables:
                    continue

                if idx_name not in existing_indexes:
                    try:
                        conn.execute(text(f'CREATE INDEX IF NOT EXISTS {idx_name} ON {table} ({columns})'))
                        logger.debug(f"Index oluşturuldu: {idx_name}")
                    except Exception as e:
                        logger.warning(f"Index oluşturma hatası {idx_name}: {e}")

            # Eski ve SQLAlchemy ix_* ile birebir çakışan redundant idx_* indekslerini temizle
            cleanup_drops = [
                "DROP INDEX IF EXISTS idx_notification_user_read",
                "DROP INDEX IF EXISTS idx_transaction_tenant_id",
                "DROP INDEX IF EXISTS idx_asset_tenant_id",
                "DROP INDEX IF EXISTS idx_recurring_plan_tenant_id",
                "DROP INDEX IF EXISTS idx_user_tenant_id",
                "DROP INDEX IF EXISTS idx_logbook_entry_tenant_id",
                "DROP INDEX IF EXISTS idx_payment_tenant_id",
                "DROP INDEX IF EXISTS idx_plan_occurrence_tenant_id",
                "DROP INDEX IF EXISTS idx_quiz_question_tenant_id",
                "DROP INDEX IF EXISTS idx_quiz_question_tenant",
                "DROP INDEX IF EXISTS idx_audit_log_timestamp",
                "DROP INDEX IF EXISTS idx_audit_log_tenant",
                "DROP INDEX IF EXISTS idx_audit_log_user",
                "DROP INDEX IF EXISTS idx_investor_profile_tenant",
                "DROP INDEX IF EXISTS idx_investor_profile_user",
                "DROP INDEX IF EXISTS idx_alert_config_user",
                "DROP INDEX IF EXISTS idx_quiz_attempt_user",
                "DROP INDEX IF EXISTS idx_quiz_attempt_tenant",
                "DROP INDEX IF EXISTS idx_tag_tenant",
                "DROP INDEX IF EXISTS idx_user_achievement_tenant",
                "DROP INDEX IF EXISTS idx_user_achievement_user",
                "DROP INDEX IF EXISTS idx_user_progress_tenant",
                "DROP INDEX IF EXISTS idx_user_progress_user",
                "DROP INDEX IF EXISTS idx_asset_transaction_tenant_id",
                "DROP INDEX IF EXISTS idx_user_username",
                "DROP INDEX IF EXISTS idx_tag_name",
            ]
            for drop_sql in cleanup_drops:
                try:
                    conn.execute(text(drop_sql))
                except Exception as e:
                    logger.debug("Index drop atlandı: %s", e)

    if ctx is not None:
        with ctx:
            return _do_index_sync()
    return _do_index_sync()
