"""
Kategori bütçelerini güncelleme scripti
Sadece standart gider kategorileri için aylık bütçe doldur
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app import app, db
from models import Category

# Standart gider kategorileri için aylık bütçeler
# Bu kategoriler seed_standard_categories.py ile veritabanına seed edilir
STANDARD_EXPENSE_BUDGETS = {
    'GDR-7001': 10000,   # Konut & Kira
    'GDR-7002': 15000,   # Faturalar (Elektrik/Su/Gaz)
    'GDR-7003': 8000,    # Market & Gıda
    'GDR-7004': 2000,    # Ulaşım & Yakıt
    'GDR-7005': 3000,    # Sağlık & Eczane
    'GDR-7006': 10000,   # Eğitim & Kurslar
    'GDR-7007': 2000,    # Giyim & Aksesuar
    'GDR-7008': 5000,    # Eğlence & Restoran
    'GDR-7009': 5000,    # Sigorta Primleri
}

def update_category_budgets():
    """Kategori bütçelerini güncelle"""
    with app.app_context():
        # Tüm kategorileri al
        all_categories = Category.query.all()
        
        print(f"Toplam kategori sayısı: {len(all_categories)}")
        
        updated_count = 0
        cleared_count = 0
        
        for category in all_categories:
            # Eğer kategori standart gider kategorisi ise bütçe doldur
            if category.code in STANDARD_EXPENSE_BUDGETS:
                category.budget_limit = STANDARD_EXPENSE_BUDGETS[category.code]
                print(f"Bütçe dolduruluyor: {category.name} ({category.code}) - {STANDARD_EXPENSE_BUDGETS[category.code]} ₺")
                updated_count += 1
            else:
                # Diğer kategorilerin bütçesini temizle
                if category.budget_limit is not None:
                    category.budget_limit = None
                    print(f"Bütçe temizleniyor: {category.name} ({category.type})")
                    cleared_count += 1
        
        db.session.commit()
        print(f"\n✅ {updated_count} standart gider kategorisine bütçe dolduruldu")
        print(f"✅ {cleared_count} kategorinin bütçesi temizlendi")

if __name__ == '__main__':
    update_category_budgets()
