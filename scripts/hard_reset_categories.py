"""
Hard Reset Kategori Scripti
Session cache'i temizleyerek ve fresh connection ile kategorileri sıfırlar.
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models import Category, db

def hard_reset_categories():
    """Session cache'i temizleyerek kategorileri sıfırlar"""
    
    # Önce session'ı temizle
    db.session.remove()
    
    # Standart kategori kodları
    standard_codes = [
        'GLR-6001', 'GLR-6002', 'GLR-6003', 'GLR-6004', 'GLR-6005',
        'GLR-6006', 'GLR-6007', 'GLR-6008',
        'GDR-7001', 'GDR-7002', 'GDR-7003', 'GDR-7004', 'GDR-7005',
        'GDR-7006', 'GDR-7007', 'GDR-7008', 'GDR-7009',
        'YTR-1001', 'YTR-1002', 'YTR-1003', 'YTR-1004', 'YTR-1005',
        'YTR-1006', 'YTR-1007'
    ]
    
    # Tüm kategorileri tekrar al (fresh query)
    all_categories = Category.query.all()
    print(f"Toplam kategori (fresh query): {len(all_categories)}")
    
    deleted_count = 0
    kept_count = 0
    
    for category in all_categories:
        # Standart kategori mi kontrol et
        if category.code in standard_codes and category.tenant_id is None:
            kept_count += 1
            print(f"  Korundu: {category.code}")
        else:
            # Standart değilse sil
            try:
                db.session.delete(category)
                deleted_count += 1
                print(f"  Silindi: {category.code or 'N/A'}")
            except Exception as e:
                print(f"  HATA: {category.code or 'N/A'} silinemedi: {str(e)[:50]}")
    
    try:
        db.session.commit()
        print(f"\n✅ Temizleme tamamlandı!")
        print(f"   Silinen: {deleted_count}")
        print(f"   Korunan: {kept_count}")
        
        # Session'ı tekrar temizle
        db.session.remove()
        
        # Final kontrol
        final_count = Category.query.count()
        print(f"   Final toplam: {final_count}")
        
    except Exception as e:
        db.session.rollback()
        print(f"❌ Commit hatası: {e}")
        raise

if __name__ == '__main__':
    from app import app
    
    with app.app_context():
        print("Hard reset kategori temizleme başlatılıyor...")
        hard_reset_categories()
