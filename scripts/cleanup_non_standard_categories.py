"""
Standart olmayan kategorileri temizleme scripti
Kullanıcıların oluşturduğu standart olmayan kategorileri siler
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app import app, db
from models import Category

# Standart kategoriler (GL kodlarına göre)
# Bu kategoriler seed_standard_categories.py ile veritabanına seed edilir
STANDARD_CATEGORIES = {
    'Gelir': {
        'GLR-6001': 'Maaş / Ücret Geliri',
        'GLR-6002': 'Avans',
        'GLR-6003': 'Kira Geliri',
        'GLR-6004': 'Temettü Geliri',
        'GLR-6005': 'Faiz Geliri',
        'GLR-6006': 'Yatırım / Sermaye Kazancı',
        'GLR-6007': 'Ek Gelir / Yan İş',
        'GLR-6008': 'Prim & İkramiye',
    },
    'Gider': {
        'GDR-7001': 'Konut & Kira',
        'GDR-7002': 'Faturalar (Elektrik/Su/Gaz)',
        'GDR-7003': 'Market & Gıda',
        'GDR-7004': 'Ulaşım & Yakıt',
        'GDR-7005': 'Sağlık & Eczane',
        'GDR-7006': 'Eğitim & Kurslar',
        'GDR-7007': 'Giyim & Aksesuar',
        'GDR-7008': 'Eğlence & Restoran',
        'GDR-7009': 'Sigorta Primleri',
    },
    'Yatırım': {
        'YTR-1001': 'Yatırıma Aktarılan',
        'YTR-1002': 'Hisse Senedi Alımı',
        'YTR-1003': 'Fon & BES Alımı',
        'YTR-1004': 'Altın Alımı',
        'YTR-1005': 'Kripto Para Alımı',
        'YTR-1006': 'Gayrimenkul Alımı',
        'YTR-1007': 'Nakit & Mevduat',
    },
    'Transfer': {
        'TRF-2001': 'Hesap Arası Transfer',
        'TRF-2002': 'Nakit Çekme',
        'TRF-2003': 'Nakit Yatırma',
        'TRF-2004': 'Diğer Transferler',
    }
}

def cleanup_non_standard_categories():
    """Standart olmayan kategorileri temizler"""
    with app.app_context():
        # Standart kategori kodlarını topla
        standard_codes = set()
        for type_categories in STANDARD_CATEGORIES.values():
            standard_codes.update(type_categories.keys())
        
        # Tüm kategorileri bul
        all_categories = Category.query.all()
        
        print(f"Toplam kategori sayısı: {len(all_categories)}")
        print(f"Standart kod sayısı: {len(standard_codes)}")
        
        deleted_count = 0
        kept_count = 0
        
        for category in all_categories:
            # Eğer kategori standart kodlardan birine sahip değilse sil
            if category.code not in standard_codes:
                try:
                    print(f"Siliniyor: {category.name} ({category.code}) - Tenant: {category.tenant_id}")
                    db.session.delete(category)
                    deleted_count += 1
                except Exception as e:
                    print(f"Kategori silinemedi (ID: {category.id}): {e}")
            else:
                kept_count += 1
        
        if deleted_count > 0:
            db.session.commit()
            print(f"\n✅ {deleted_count} standart olmayan kategori temizlendi")
            print(f"✅ {kept_count} standart kategori korundu")
        else:
            print(f"\nℹ️  Temizlenecek standart olmayan kategori bulunamadı")
            print(f"ℹ️  {kept_count} standart kategori zaten mevcut")

if __name__ == '__main__':
    cleanup_non_standard_categories()
