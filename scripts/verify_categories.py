"""
Kategori Doğrulama Scripti
Standart kategorilerin doğru şekilde oluşturulduğunu doğrular.
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models import Category

def verify_categories():
    """Standart kategorileri doğrular"""
    
    # Standart kategori kodları (GL standart formatı)
    standard_codes = [
        'GLR-6001', 'GLR-6002', 'GLR-6003', 'GLR-6004', 'GLR-6005',
        'GLR-6006', 'GLR-6007', 'GLR-6008',
        'GDR-7001', 'GDR-7002', 'GDR-7003', 'GDR-7004', 'GDR-7005',
        'GDR-7006', 'GDR-7007', 'GDR-7008', 'GDR-7009',
        'YTR-1001', 'YTR-1002', 'YTR-1003', 'YTR-1004', 'YTR-1005',
        'YTR-1006', 'YTR-1007'
    ]
    
    # Tüm sistem genelinde kategorileri al (sadece tenant_id=None)
    all_system_categories = Category.query.filter_by(tenant_id=None).all()
    
    print(f"Toplam sistem genelinde kategori: {len(all_system_categories)}")
    print(f"Beklenen standart kategori sayısı: {len(standard_codes)}")
    print()
    
    # Her standart kod için kontrol et
    missing_codes = []
    for code in standard_codes:
        cat = Category.query.filter_by(code=code, tenant_id=None).first()
        if cat:
            print(f"✓ {code} - {cat.name} - {cat.type} - Bütçe: {cat.budget_limit} ₺")
        else:
            missing_codes.append(code)
            print(f"✗ {code} - BULUNAMADI")
    
    print()
    if missing_codes:
        print(f"❌ Eksik kategoriler: {len(missing_codes)}")
        for code in missing_codes:
            print(f"   - {code}")
    else:
        print("✅ Tüm standart kategoriler mevcut!")
    
    # Fazlı kategorileri kontrol et
    extra_categories = [cat for cat in all_system_categories if cat.code not in standard_codes]
    if extra_categories:
        print(f"\n⚠️  Fazlı kategoriler: {len(extra_categories)}")
        for cat in extra_categories:
            print(f"   - {cat.code or 'N/A'} - {cat.name}")
    else:
        print("✅ Fazlı kategori yok!")

if __name__ == '__main__':
    from app import app
    
    with app.app_context():
        verify_categories()
