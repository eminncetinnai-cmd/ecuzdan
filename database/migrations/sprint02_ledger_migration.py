import hashlib
import logging
import os
import sys
from decimal import Decimal

# Uygulama kök dizinini yola ekle
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from app import app
from domain.ledger.models.ledger_models import Account, JournalEntry, LedgerLine
from models import Category, Tenant, Transaction
from shared.db import db

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger('Sprint02_Migration')

def create_tables():
    """Yeni tabloları oluşturur."""
    logger.info("Yeni tablolar (Account, JournalEntry, LedgerLine) oluşturuluyor...")
    db.create_all()
    logger.info("Tablolar oluşturuldu.")

def migrate_categories_to_accounts():
    """Mevcut Kategorileri Account tablosuna taşır."""
    logger.info("Kategoriler Account tablosuna taşınıyor...")
    categories = Category.query.all()
    tenants = Tenant.query.all()

    count = 0
    for tenant in tenants:
        for cat in categories:
            # Check if exists
            existing = Account.query.filter_by(tenant_id=tenant.id, name=cat.name).first()
            if not existing:
                acct_type = 'Revenue' if cat.type == 'Gelir' else 'Expense'
                new_acct = Account(
                    tenant_id=tenant.id,
                    name=cat.name,
                    type=acct_type,
                    currency=tenant.base_currency or 'TRY'
                )
                db.session.add(new_acct)
                count += 1

        # Her tenant için varsayılan bir Kasa hesabı oluşturalım
        cash_acct = Account.query.filter_by(tenant_id=tenant.id, name='Nakit Kasa', type='Asset').first()
        if not cash_acct:
            db.session.add(Account(
                tenant_id=tenant.id,
                name='Nakit Kasa',
                type='Asset',
                currency=tenant.base_currency or 'TRY'
            ))

    db.session.commit()
    logger.info(f"{count} adet hesap başarıyla oluşturuldu.")

def calculate_hash(date, description, debit_sum, credit_sum, previous_hash=None):
    """Journal Entry için basit bir SHA-256 hash hesaplar."""
    raw_str = f"{date}|{description}|{debit_sum}|{credit_sum}|{previous_hash or 'GENESIS'}"
    return hashlib.sha256(raw_str.encode('utf-8')).hexdigest()

def migrate_transactions():
    """Transaction kayıtlarını JournalEntry ve LedgerLine'a dönüştürür."""
    logger.info("Transaction'lar JournalEntry formatına dönüştürülüyor...")

    # Tüm transactionları tarih sırasına göre al
    transactions = Transaction.query.order_by(Transaction.date.asc(), Transaction.id.asc()).all()

    last_hash_by_tenant = {}
    je_count = 0
    ll_count = 0

    # Tenant tabanlı Default Kasa hesaplarını cache'le
    cash_accounts = {
        acct.tenant_id: acct
        for acct in Account.query.filter_by(name='Nakit Kasa', type='Asset').all()
    }

    for txn in transactions:
        cash_acct = cash_accounts.get(txn.tenant_id)
        if not cash_acct:
            continue

        target_acct = Account.query.filter_by(tenant_id=txn.tenant_id, name=txn.category).first()
        if not target_acct:
            # Fallback
            target_acct = cash_acct

        prev_hash = last_hash_by_tenant.get(txn.tenant_id)

        # Hash hesaplama
        new_hash = calculate_hash(
            date=txn.date,
            description=txn.description or txn.category,
            debit_sum=float(txn.amount),
            credit_sum=float(txn.amount),
            previous_hash=prev_hash
        )

        je = JournalEntry(
            tenant_id=txn.tenant_id,
            date=txn.date,
            description=txn.description or txn.category,
            hash=new_hash,
            previous_hash=prev_hash,
            status='Posted'
        )
        db.session.add(je)
        db.session.flush() # ID almak için

        # LedgerLines oluştur
        if txn.type == 'Gelir':
            # Gelir: Kasa (Debit), Gelir Hesabı (Credit)
            line1 = LedgerLine(journal_entry_id=je.id, account_id=cash_acct.id, debit=txn.amount, credit=Decimal('0.0000'))
            line2 = LedgerLine(journal_entry_id=je.id, account_id=target_acct.id, debit=Decimal('0.0000'), credit=txn.amount)
        else:
            # Gider vb: Kasa (Credit), Gider Hesabı (Debit)
            line1 = LedgerLine(journal_entry_id=je.id, account_id=cash_acct.id, debit=Decimal('0.0000'), credit=txn.amount)
            line2 = LedgerLine(journal_entry_id=je.id, account_id=target_acct.id, debit=txn.amount, credit=Decimal('0.0000'))

        db.session.add(line1)
        db.session.add(line2)

        last_hash_by_tenant[txn.tenant_id] = new_hash
        je_count += 1
        ll_count += 2

    db.session.commit()
    logger.info(f"{je_count} adet Journal Entry ve {ll_count} adet Ledger Line oluşturuldu.")

def main():
    logger.info("Sprint-02 Ledger Migration başlatılıyor...")
    with app.app_context():
        create_tables()
        migrate_categories_to_accounts()
        migrate_transactions()

    logger.info("Migration tamamlandı.")

if __name__ == '__main__':
    main()
