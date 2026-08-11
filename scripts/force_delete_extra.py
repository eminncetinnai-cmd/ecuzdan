"""
Zorunlu Silme Scripti
Fazlı kategorileri zorla siler (raw SQL kullanarak).
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models import Category, db

def force_delete_extra():
    """Fazlı kategorileri raw SQL ile siler"""
    
    # Fazlı kategori kodları (GLR-6009 hariç - referansı var)
    extra_codes = [
        'GLR-6010', 'GLR-6011',
        'GDR-7010', 'GDR-7011', 'GDR-7012', 'GDR-7013', 'GDR-7014', 
        'GDR-7015', 'GDR-7016', 'GDR-7017', 'GDR-7018', 'GDR-7019', 'GDR-7020',
        'YTR-1008'
    ]
    
    deleted_count = 0
    
    for code in extra_codes:
        try:
            # Raw SQL ile sil
            result = db.session.execute(db.text("DELETE FROM category WHERE code = :code"), {'code': code})
            if result.rowcount > 0:
                deleted_count += 1
                print(f"  Silindi: {code}")
            else:
                print(f"  Bulunamadı: {code}")
        except Exception as e:
            print(f"  HATA: {code} silinemedi: {str(e)[:50]}")
    
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
        print("Fazlı kategoriler zorla siliniyor...\n")
        force_delete_extra()
