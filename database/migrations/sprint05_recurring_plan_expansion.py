"""
Sprint 05 — RecurringPlan ve Asset Genişletmesi
===========================================
Amaç: Faz 1 kapsamındaki DCA, Abonelik, Kira tipleri için
RecurringPlan ve Asset tablolarına gerekli sütunların eklenmesi.

Çalıştırma:
  python database/migrations/sprint05_recurring_plan_expansion.py
"""

import logging
import os
import sqlite3

logger = logging.getLogger("Migration_Sprint05")
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'e_cuzdan_v15.db'))

def run_migration():
    if not os.path.exists(DB_PATH):
        logger.error(f"Veritabanı bulunamadı: {DB_PATH}")
        return

    logger.info(f"Bağlanılan Veritabanı: {DB_PATH}")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        # 1. RecurringPlan sütunları
        plan_columns = [
            "ALTER TABLE recurring_plan ADD COLUMN plan_type VARCHAR(20) DEFAULT 'Taksit' NOT NULL;",
            "ALTER TABLE recurring_plan ADD COLUMN end_date VARCHAR(10);",
            "ALTER TABLE recurring_plan ADD COLUMN frequency VARCHAR(20) DEFAULT 'Aylık' NOT NULL;",
            "ALTER TABLE recurring_plan ADD COLUMN status VARCHAR(20) DEFAULT 'Aktif' NOT NULL;",
            "ALTER TABLE recurring_plan ADD COLUMN target_asset_id INTEGER REFERENCES asset(id);"
        ]

        for sql in plan_columns:
            try:
                cursor.execute(sql)
                logger.info(f"Başarılı: {sql}")
            except sqlite3.OperationalError as e:
                if 'duplicate column name' in str(e).lower():
                    logger.info(f"Sütun zaten var atlanıyor: {sql}")
                else:
                    logger.error(f"Hata: {e}")
                    raise

        # Mevcut planları Taksit olarak güncelle
        try:
            cursor.execute("UPDATE recurring_plan SET plan_type = 'Taksit', frequency = 'Aylık', status = 'Aktif' WHERE plan_type = 'installment' OR plan_type = 'Taksit';")
            logger.info("Mevcut planlar Taksit olarak güncellendi.")
        except Exception as e:
            logger.error(f"Veri güncelleme hatası: {e}")

        # 2. Asset sütunları
        asset_columns = [
            "ALTER TABLE asset ADD COLUMN rent_plan_id INTEGER REFERENCES recurring_plan(id);",
            "ALTER TABLE asset ADD COLUMN dividend_yield NUMERIC(6,4);"
        ]

        for sql in asset_columns:
            try:
                cursor.execute(sql)
                logger.info(f"Başarılı: {sql}")
            except sqlite3.OperationalError as e:
                if 'duplicate column name' in str(e).lower():
                    logger.info(f"Sütun zaten var atlanıyor: {sql}")
                else:
                    logger.error(f"Hata: {e}")
                    raise

        conn.commit()
        logger.info("Sprint 05 Migrasyonu başarıyla tamamlandı.")
    finally:
        conn.close()

if __name__ == '__main__':
    run_migration()
