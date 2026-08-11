"""
Zorunlu Tüm Fazlı Kategori Silme Scripti
Raw SQL ile tüm fazlı kategorileri siler.
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models import Category, db

def force_delete_all_extra():
    """Tüm fazlı kategorileri raw SQL ile siler"""
    
    # Standart kategori kodları
    standard_codes = [
        'GLR-6001', 'GLR-6002', 'GLR-6003', 'GLR-6004', 'GLR-6005',
        'GLR-6006', 'GLR-6007', 'GLR-6008',
        'GDR-7001', 'GDR-7002', 'GDR-7003', 'GDR-7004', 'GDR-7005',
        'GDR-7006', 'GDR-7007', 'GDR-7008', 'GDR-7009',
        'YTR-1001', 'YTR-1002', 'YTR-1003', 'YTR-1004', 'YTR-1005',
        'YTR-1006', 'YTR-1007'
    ]
    
    # Tüm standart olmayanları sil
    placeholders = ','.join([':code' + str(i) for i in range(len(standard_codes))])
    params = {f'code{i}': code for i, code in enumerate(standard_codes)}
    
    try:
        # Raw SQL ile sil
        result = db.session.execute(
            db.text(f"DELETE FROM category WHERE code NOT IN ({placeholders}) AND tenant_id IS NULL"),
            params
        )
        deleted_count = result.rowcount
        print(f"Silinen kategori: {deleted_count}")
        
        db.session.commit()
        print(f"✅ İşlem tamamlandı!")
        
    except Exception as e:
        db.session.rollback()
        print(f"❌ Hata: {e}")
        raise

if __name__ == '__main__':
    from app import app
    
    with app.app_context():
        print("Tüm fazlı kategoriler zorla siliniyor...")
        force_delete_all_extra()
