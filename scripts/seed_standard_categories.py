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
    ('GLR-6002', 'Serbest Meslek / Danışmanlık', 'Gelir', 2, 50000),
    ('GLR-6003', 'Kira Geliri', 'Gelir', 3, 30000),
    ('GLR-6004', 'Temettü Geliri', 'Gelir', 4, 20000),
    ('GLR-6005', 'Faiz Geliri', 'Gelir', 5, 25000),
    ('GLR-6006', 'Yatırım / Sermaye Kazancı', 'Gelir', 6, 50000),
    ('GLR-6007', 'Ek Gelir / Yan İş', 'Gelir', 7, 15000),
    ('GLR-6008', 'Prim & İkramiye', 'Gelir', 8, 100000),
    ('GLR-6009', 'Avans', 'Gelir', 9, 50000),
    
    # Gider Kategorileri (GDR-7xxx - 700 Hesap Grubu) - Gerçekçi aylık limitler
    ('GDR-7001', 'Konut & Kira', 'Gider', 1, 10000),
    ('GDR-7002', 'Faturalar (Elektrik/Su/Gaz)', 'Gider', 2, 15000),
    ('GDR-7003', 'Market & Gıda', 'Gider', 3, 8000),
    ('GDR-7004', 'Ulaşım & Yakıt', 'Gider', 4, 2000),
    ('GDR-7005', 'Sağlık & Eczane', 'Gider', 5, 3000),
    ('GDR-7006', 'Eğitim & Kurslar', 'Gider', 6, 10000),
    ('GDR-7007', 'Giyim & Aksesuar', 'Gider', 7, 2000),
    ('GDR-7008', 'Eğlence & Restoran', 'Gider', 8, 5000),
    ('GDR-7009', 'Sigorta Primleri', 'Gider', 9, 5000),
    ('GDR-7010', 'Vergi', 'Gider', 10, 20000),
    ('GDR-7011', 'Kredi', 'Gider', 11, 100000),
    ('GDR-7012', 'Kredi Kartı', 'Gider', 12, 50000),
    
    # Yatırım Kategorileri (YTR-1xxx - 100 Varlık Hesabı) - Yatırım limitleri
    ('YTR-1001', 'Yatırıma Aktarılan', 'Yatırım', 1, 50000),
    ('YTR-1002', 'Hisse Senedi Alımı', 'Yatırım', 2, 30000),
    ('YTR-1003', 'Fon & BES Alımı', 'Yatırım', 3, 50000),
    ('YTR-1004', 'Altın Alımı', 'Yatırım', 4, 200000),
    ('YTR-1005', 'Kripto Para Alımı', 'Yatırım', 5, 50000),
    ('YTR-1006', 'Gayrimenkul Alımı', 'Yatırım', 6, 20000),
    ('YTR-1007', 'Nakit & Mevduat', 'Yatırım', 7, 100000),
    
    # Transfer Kategorileri (TRF-2xxx - 200 Transfer Hesabı) - Transfer limitleri
    ('TRF-2001', 'Hesap Arası Transfer', 'Transfer', 1, 100000),
    ('TRF-2002', 'Nakit Çekme', 'Transfer', 2, 50000),
    ('TRF-2003', 'Nakit Yatırma', 'Transfer', 3, 50000),
    ('TRF-2004', 'Diğer Transferler', 'Transfer', 4, 50000),
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
        print(f"   Toplam standart kategori: {len(standard_categories)}")
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
