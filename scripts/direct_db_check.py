"""
Doğrudan Veritabanı Kontrol Scripti
Flask app context kullanarak veritabanını kontrol eder.
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models import Category

def check_db_directly():
    """Flask app context ile veritabanını kontrol eder"""
    
    # Standart kategori kodları
    standard_codes = [
        'GLR-6001', 'GLR-6002', 'GLR-6003', 'GLR-6004', 'GLR-6005',
        'GLR-6006', 'GLR-6007', 'GLR-6008',
        'GDR-7001', 'GDR-7002', 'GDR-7003', 'GDR-7004', 'GDR-7005',
        'GDR-7006', 'GDR-7007', 'GDR-7008', 'GDR-7009',
        'YTR-1001', 'YTR-1002', 'YTR-1003', 'YTR-1004', 'YTR-1005',
        'YTR-1006', 'YTR-1007'
    ]
    
    # Tüm sistem genelinde kategorileri al
    all_system_categories = Category.query.filter_by(tenant_id=None).all()
    
    print(f"Toplam sistem genelinde kategori: {len(all_system_categories)}")
    print(f"Beklenen standart kategori sayısı: {len(standard_codes)}")
    
    print(f"\nStandart kategori kontrolü:")
    for code in standard_codes:
        cat = Category.query.filter_by(code=code, tenant_id=None).first()
        if cat:
            print(f"  ✓ {code} - {cat.name}")
        else:
            print(f"  ✗ {code} - BULUNAMADI")
    
    # Fazlı kategorileri bul
    extra_categories = [c for c in all_system_categories if c.code not in standard_codes]
    
    if extra_categories:
        print(f"\nFazlı kategoriler: {len(extra_categories)}")
        for cat in extra_categories:
            print(f"  - {cat.code or 'N/A'} - {cat.name}")
    else:
        print(f"\n✅ Fazlı kategori yok!")

if __name__ == '__main__':
    from app import app
    
    with app.app_context():
        check_db_directly()
