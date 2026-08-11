"""
Zorunlu Kategori Temizleme Scripti
Sadece standart kategorileri bırakır, diğerlerini siler.
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models import Category, db

def force_cleanup_categories():
    """Sadece standart kategorileri bırakır, diğerlerini siler"""
    
    # Standart kategori kodları (GL standart formatı)
    standard_codes = [
        'GLR-6001', 'GLR-6002', 'GLR-6003', 'GLR-6004', 'GLR-6005',
        'GLR-6006', 'GLR-6007', 'GLR-6008',
        'GDR-7001', 'GDR-7002', 'GDR-7003', 'GDR-7004', 'GDR-7005',
        'GDR-7006', 'GDR-7007', 'GDR-7008', 'GDR-7009',
        'YTR-1001', 'YTR-1002', 'YTR-1003', 'YTR-1004', 'YTR-1005',
        'YTR-1006', 'YTR-1007'
    ]
    
    # Tüm kategorileri al
    all_categories = Category.query.all()
    
    deleted_count = 0
    kept_count = 0
    error_count = 0
    
    for category in all_categories:
        # Standart kategori mi kontrol et
        if category.code in standard_codes and category.tenant_id is None:
            kept_count += 1
            print(f"  Korundu: {category.code} - {category.name}")
        else:
            # Standart değilse sil
            try:
                db.session.delete(category)
                deleted_count += 1
                print(f"  Silindi: {category.code or 'N/A'} - {category.name} (tenant_id: {category.tenant_id})")
            except Exception as e:
                error_count += 1
                print(f"  HATA: {category.code or 'N/A'} - {category.name} silinemedi: {str(e)[:50]}")
    
    try:
        db.session.commit()
        print(f"\n✅ Temizleme tamamlandı!")
        print(f"   Silinen kategori: {deleted_count}")
        print(f"   Korunan kategori: {kept_count}")
        print(f"   Hata alan kategori: {error_count}")
        print(f"   Toplam işlem: {len(all_categories)}")
    except Exception as e:
        db.session.rollback()
        print(f"\n❌ Commit hatası oluştu: {e}")
        raise

if __name__ == '__main__':
    from app import app
    
    with app.app_context():
        print("Zorunlu kategori temizleme başlatılıyor...\n")
        force_cleanup_categories()
