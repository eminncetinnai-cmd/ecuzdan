"""
Fazlı Kategori Silme Scripti
Spesifik fazlı kategorileri koduna göre siler.
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models import Category, db

def delete_extra_categories():
    """Fazlı kategorileri koduna göre siler"""
    
    # Fazlı kategori kodları (referansı olmayanlar)
    extra_codes = [
        'GLR-6010', 'GLR-6011',
        'GDR-7010', 'GDR-7011', 'GDR-7012', 'GDR-7013', 'GDR-7014', 
        'GDR-7015', 'GDR-7016', 'GDR-7017', 'GDR-7018', 'GDR-7019', 'GDR-7020',
        'YTR-1008'
    ]
    
    deleted_count = 0
    
    for code in extra_codes:
        cat = Category.query.filter_by(code=code).first()
        if cat:
            try:
                db.session.delete(cat)
                deleted_count += 1
                print(f"  Silindi: {code} - {cat.name}")
            except Exception as e:
                print(f"  HATA: {code} silinemedi: {str(e)[:50]}")
        else:
            print(f"  Bulunamadı: {code}")
    
    try:
        db.session.commit()
        print(f"\n✅ İşlem tamamlandı!")
        print(f"   Silinen kategori: {deleted_count}")
    except Exception as e:
        db.session.rollback()
        print(f"\n❌ Commit hatası: {e}")
        raise

if __name__ == '__main__':
    from app import app
    
    with app.app_context():
        print("Fazlı kategoriler siliniyor...\n")
        delete_extra_categories()
