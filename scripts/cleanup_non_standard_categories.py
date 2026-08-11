"""
Standart olmayan kategorileri temizleme scripti
Kullanıcıların oluşturduğu standart olmayan kategorileri siler
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app import app, db
from models import Category
from scripts.seed_standard_categories import STANDARD_CATEGORIES

def cleanup_non_standard_categories():
    """Standart olmayan kategorileri temizler"""
    with app.app_context():
        # Standart kategori kodlarını topla (list format)
        standard_codes = set()
        for code, name, type_, sort_order, budget_limit in STANDARD_CATEGORIES:
            standard_codes.add(code)
        
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
