import sys
import os
import logging

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from sqlalchemy import text
from shared.db import db
from models import Category, Account


logger = logging.getLogger("Migration_Sprint03")


def run_sprint03_migration():
    """Kategori tablosunu v2 standartlarına yükseltir (SQLite tam uyumlu)"""
    logger.info("Sprint 03 Category Migration Başlatılıyor...")

    # 1. Yeni Kolonların SQLite Uyumlu Eklendiğinin Doğrulanması (ALTER TABLE)
    columns_to_add = [
        ("code", "VARCHAR(30)"),
        ("names", "JSON"),
        ("description", "JSON"),
        ("sort_order", "INTEGER DEFAULT 0"),
        ("account_id", "INTEGER"),
        ("tax_rate", "NUMERIC(5,2) DEFAULT 0.00"),
        ("version", "INTEGER DEFAULT 1"),
        ("created_by", "INTEGER"),
        ("created_at", "DATETIME"),
        ("updated_by", "INTEGER"),
        ("updated_at", "DATETIME"),
    ]

    with db.engine.connect() as conn:
        existing_cols = [row[1] for row in conn.execute(text("PRAGMA table_info(category)"))]

        for col_name, col_type in columns_to_add:
            if col_name not in existing_cols:
                try:
                    conn.execute(text(f"ALTER TABLE category ADD COLUMN {col_name} {col_type}"))
                    logger.info(f"Kolon Ekleniyor: category.{col_name}")
                except Exception as e:
                    logger.warning(f"Kolon eklenemedi (zaten var olabilir): {col_name} -> {e}")
        conn.commit()

    # 2. Kod, Çoklu Dil ve Hiyerarşi Verilerinin Normalize Edilmesi
    categories = Category.query.all()
    for cat in categories:
        # Code Alanını Otomatik Üret (Eğer Yoksa)
        if not cat.code:
            prefix = "GLR" if cat.type == "Gelir" else ("GDR" if cat.type == "Gider" else "YTR")
            cat.code = f"{prefix}-{cat.id:04d}"

        # Names & Description JSON Nesnelerini Doldur
        if not cat.names:
            cat.names = {"tr": cat.name, "en": cat.name}

        # Path Hesabı
        if not cat.path:
            cat.path = f"/{cat.id}/" if not cat.parent_id else f"/{cat.parent_id}/{cat.id}/"

        # Version Defaults
        if not cat.version:
            cat.version = 1

    db.session.commit()
    logger.info("Kategori Temel Verileri Dönüştürüldü.")

    # 3. Transaction ve Account (Ledger) Bağlantılarının Kurulması
    try:
        accounts = Account.query.all()
        accounts_by_name = {a.name: a.id for a in accounts}
        for cat in Category.query.all():
            if not cat.account_id and cat.name in accounts_by_name:
                cat.account_id = accounts_by_name[cat.name]
        db.session.commit()
        logger.info("Category-Account (Ledger) Bağlantıları Kuruldu.")
    except Exception as e:
        logger.warning(f"Account eşleştirme atlandı: {e}")

    logger.info("Sprint 03 Category Migration Başarıyla Tamamlandı.")


if __name__ == "__main__":
    from app import app
    with app.app_context():
        run_sprint03_migration()
