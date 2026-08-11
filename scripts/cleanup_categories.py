"""
Kategori Temizleme Scripti
Bu script standart olmayan kategorileri ve bu kategorilere ait transaction'ları temizler.
Sadece 4 standart kategori bırakır: Gelir, Gider, Yatırım, Transfer
"""

import sys
import os

# Proje kök dizinini Python path'ine ekle
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models import Category, Transaction, db

def cleanup_categories_and_transactions():
    """Standart olmayan kategorileri ve transaction'ları temizler"""
    
    # Standart kategori isimleri
    standard_categories = ['Gelir', 'Gider', 'Yatırım', 'Transfer']
    
    # Tüm kategorileri al (tenant_id=None olan sistem kategorileri)
    all_categories = Category.query.filter_by(tenant_id=None).all()
    
    deleted_category_count = 0
    kept_category_count = 0
    deleted_transaction_count = 0
    
    for category in all_categories:
        # Standart kategori mi kontrol et
        if category.name in standard_categories:
            kept_category_count += 1
            print(f"  Korundu: {category.name} (type: {category.type})")
        else:
            # Standart değilse, önce bu kategoriye ait transaction'ları sil
            transactions = Transaction.query.filter_by(category=category.name).all()
            for tx in transactions:
                db.session.delete(tx)
                deleted_transaction_count += 1
            
            # Kategoriyi sil
            db.session.delete(category)
            deleted_category_count += 1
            print(f"  Silindi: {category.name} (type: {category.type}, transaction: {len(transactions)})")
    
    try:
        db.session.commit()
        print(f"\n✅ Temizleme tamamlandı!")
        print(f"   Silinen kategori: {deleted_category_count}")
        print(f"   Korunan kategori: {kept_category_count}")
        print(f"   Silinen transaction: {deleted_transaction_count}")
        print(f"   Toplam işlem: {len(all_categories)}")
    except Exception as e:
        db.session.rollback()
        print(f"\n❌ Hata oluştu: {e}")
        raise

if __name__ == '__main__':
    # Flask uygulamasını oluştur
    from app import app
    
    with app.app_context():
        print("Kategoriler ve transaction'lar temizleniyor...\n")
        cleanup_categories_and_transactions()
