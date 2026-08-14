"""
Standart Kategori Seed Scripti
Bu script standart kategorileri veritabanına ekler.
Kategoriler tenant_id=None ile sistem genelinde oluşturulur (silinemez).
"""

import sys
import os

# Proje kök dizinini Python path'ine ekle
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models import Category, db
from shared.db import db as shared_db
from flask import Flask

# Standart kategoriler - GL kodları ile bütçe limitleri
# Bu liste diğer modüller tarafından da import edilebilir
STANDARD_CATEGORIES = [
    # Gelir Kategorileri (GLR-6xxx - 600 Hesap Grubu) - Gelir kategorileri için yüksek limit
    ('GLR-6001', 'Maaş / Ücret Geliri', 'Gelir', 1, 100000),
    ('GLR-6002', 'Avans', 'Gelir', 2, 50000),
    ('GLR-6003', 'Ek Gelir / Diğer Gelirler', 'Gelir', 3, 15000),
    ('GLR-6004', 'Faiz Geliri', 'Gelir', 4, 25000),
    ('GLR-6005', 'Kira Geliri', 'Gelir', 5, 30000),
    ('GLR-6006', 'Prim & İkramiye', 'Gelir', 6, 100000),
    ('GLR-6007', 'Yardım & Destek', 'Gelir', 7, 20000),
    ('GLR-6008', 'Yatırım Kazancı', 'Gelir', 8, 50000),
    
    # Gider Kategorileri (GDR-7xxx - 700 Hesap Grubu) - Gerçekçi aylık limitler
    ('GDR-7001', 'Kredi Kartı Ödemesi', 'Gider', 1, 50000),
    ('GDR-7002', 'Kredi Ödemeleri', 'Gider', 2, 100000),
    ('GDR-7003', 'Aylık Sabit Gider', 'Gider', 3, 20000),
    ('GDR-7004', 'Bağış & Yardım', 'Gider', 4, 10000),
    ('GDR-7005', 'Eğitim & Kurslar', 'Gider', 5, 10000),
    ('GDR-7006', 'Kira', 'Gider', 6, 10000),
    ('GDR-7007', 'Kişisel Bakım', 'Gider', 7, 3000),
    ('GDR-7008', 'Nafaka', 'Gider', 8, 5000),
    ('GDR-7009', 'Diğer Giderler', 'Gider', 9, 5000),
    
    # Yatırım Kategorileri (YTR-1xxx - 100 Varlık Hesabı) - Yatırım limitleri
    ('YTR-1001', 'Altın Alımı', 'Yatırım', 1, 200000),
    ('YTR-1002', 'Diğer Yatırımlar', 'Yatırım', 2, 50000),
    ('YTR-1003', 'Fon', 'Yatırım', 3, 50000),
    ('YTR-1004', 'Gayrimenkul', 'Yatırım', 4, 20000),
    ('YTR-1005', 'Hisse Senedi', 'Yatırım', 5, 30000),
    ('YTR-1006', 'Kripto', 'Yatırım', 6, 50000),
    ('YTR-1007', 'Nakit & Mevduat', 'Yatırım', 7, 100000),
]

def seed_standard_categories():
    """Standart kategorileri veritabanına ekler"""
    
    added_count = 0
    updated_count = 0
    
    for code, name, type_, sort_order, budget_limit in STANDARD_CATEGORIES:
        # Kategori zaten var mı kontrol et (koda göre)
        existing = Category.query.filter_by(code=code).first()
        if existing:
            # Kategori varsa sil ve yeniden oluştur
            db.session.delete(existing)
            db.session.flush()
        
        # Kategori oluştur - tenant_id NULL ile (sistem genelinde)
        db.session.add(Category(
            code=code,
            name=name,
            type=type_,
            sort_order=sort_order,
            is_active=True,
            tenant_id=None,  # Sistem genelinde, silinemez
            level=0,
            path=f"/",
            budget_limit=budget_limit  # Bütçe limiti eklendi
        ))
        added_count += 1
        print(f"✓ Eklendi: {code} - {name} ({type_}) - Bütçe: {budget_limit} ₺")
    
    try:
        db.session.commit()
        print(f"\n✅ İşlem tamamlandı!")
        print(f"   Yeni eklenen: {added_count}")
        print(f"   Güncellenen: {updated_count}")
        print(f"   Toplam standart kategori: {len(STANDARD_CATEGORIES)}")
    except Exception as e:
        db.session.rollback()
        print(f"\n❌ Hata oluştu: {e}")
        raise

if __name__ == '__main__':
    # Flask uygulamasını oluştur
    from app import app
    
    with app.app_context():
        print("Standart kategoriler veritabanına ekleniyor...\n")
        seed_standard_categories()

