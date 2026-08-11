"""
Eski Transaction Temizleme Scripti
Standart olmayan kategorilere sahip transaction'ları temizler
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app, db
from models import Transaction, Category

def cleanup_old_transactions():
    """Standart olmayan kategorilere sahip transaction'ları temizler"""
    
    with app.app_context():
        # Standart kategori isimleri
        standard_categories = [
            'Maaş / Ücret Geliri', 'Avans', 'Ek Gelir / Diğer Gelirler', 
            'Faiz Geliri', 'Kira Geliri', 'Prim & İkramiye', 
            'Yardım & Destek', 'Yatırım Kazancı',
            'Kredi Kartı Ödemesi', 'Kredi Ödemeleri', 'Aylık Sabit Gider', 
            'Bağış & Yardım', 'Eğitim & Kurslar', 'Kira', 
            'Kişisel Bakım', 'Nafaka', 'Diğer Giderler',
            'Altın Alımı', 'Diğer Yatırımlar', 'Fon', 
            'Gayrimenkul', 'Hisse Senedi', 'Kripto', 'Nakit & Mevduat',
            'Transfer'
        ]
        
        # Eski kategori eşleşmeleri
        category_mapping = {
            'Maaş': 'Maaş / Ücret Geliri',
            'Yatırıma Aktarılan': 'Diğer Yatırımlar'
        }
        
        # Tüm transaction'ları al
        all_transactions = Transaction.query.filter_by(is_deleted=False).all()
        
        updated_count = 0
        deleted_count = 0
        
        for tx in all_transactions:
            if tx.category not in standard_categories:
                # Eğer eşleşme varsa güncelle
                if tx.category in category_mapping:
                    old_category = tx.category
                    tx.category = category_mapping[tx.category]
                    updated_count += 1
                    print(f"  Güncellendi: {old_category} -> {category_mapping[old_category]}")
                else:
                    # Eşleşme yoksa sil
                    db.session.delete(tx)
                    deleted_count += 1
                    print(f"  Silindi: {tx.category} ({tx.date})")
        
        try:
            db.session.commit()
            print(f"\n✅ Temizleme tamamlandı!")
            print(f"   Güncellenen transaction: {updated_count}")
            print(f"   Silinen transaction: {deleted_count}")
            print(f"   Toplam işlem: {len(all_transactions)}")
        except Exception as e:
            db.session.rollback()
            print(f"\n❌ Hata oluştu: {e}")
            raise

if __name__ == '__main__':
    cleanup_old_transactions()
