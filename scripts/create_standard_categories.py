"""
Standart kategorileri oluşturma scripti
Sadece 4 temel kategori oluşturur: Gelir, Gider, Yatırım, Transfer
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app import app, db
from models import Category

# Standart kategoriler (sadece 4 temel kategori)
STANDARD_CATEGORIES = [
    {'name': 'Gelir', 'type': 'Gelir'},
    {'name': 'Gider', 'type': 'Gider'},
    {'name': 'Yatırım', 'type': 'Yatırım'},
    {'name': 'Transfer', 'type': 'Transfer'},
]

def create_standard_categories():
    """Standart kategorileri oluşturur"""
    with app.app_context():
        # Mevcut kategorileri kontrol et
        existing_categories = Category.query.filter_by(tenant_id=None).all()
        existing_names = {cat.name for cat in existing_categories}
        
        print(f"Mevcut sistem kategorisi sayısı: {len(existing_categories)}")
        
        created_count = 0
        skipped_count = 0
        
        for category_data in STANDARD_CATEGORIES:
            name = category_data['name']
            category_type = category_data['type']
            
            # Eğer kategori zaten varsa atla
            if name in existing_names:
                print(f"Zaten var: {name} ({category_type})")
                skipped_count += 1
                continue
            
            # Yeni kategori oluştur
            new_category = Category(
                name=name,
                type=category_type,
                tenant_id=None,  # Sistem genelinde geçerli
                budget_limit=None
            )
            
            try:
                db.session.add(new_category)
                print(f"Oluşturuluyor: {name} ({category_type})")
                created_count += 1
            except Exception as e:
                print(f"Kategori oluşturulamadı ({name}): {e}")
        
        if created_count > 0:
            db.session.commit()
            print(f"\n✅ {created_count} standart kategori oluşturuldu")
            print(f"✅ {skipped_count} kategori zaten mevcuttu")
        else:
            print(f"\nℹ️  Tüm standart kategoriler zaten mevcut")
            print(f"ℹ️  {skipped_count} kategori atlandı")

if __name__ == '__main__':
    create_standard_categories()
