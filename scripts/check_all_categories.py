"""
Tüm Kategori Kontrol Scripti
Veritabanındaki tüm kategorileri gösterir.
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models import Category

def check_all_categories():
    """Tüm kategorileri listeler"""
    
    # Tüm kategorileri al
    all_categories = Category.query.all()
    
    print(f"Toplam kategori: {len(all_categories)}")
    print()
    
    # Tenant_id None olanlar
    system_cats = [c for c in all_categories if c.tenant_id is None]
    print(f"Sistem genelinde (tenant_id=None): {len(system_cats)}")
    for cat in system_cats:
        print(f"  {cat.code or 'N/A'} - {cat.name} - {cat.type}")
    
    # Tenant_id dolu olanlar
    tenant_cats = [c for c in all_categories if c.tenant_id is not None]
    print(f"\nTenant'a özel (tenant_id dolu): {len(tenant_cats)}")
    for cat in tenant_cats:
        print(f"  {cat.code or 'N/A'} - {cat.name} - {cat.type} - tenant: {cat.tenant_id}")

if __name__ == '__main__':
    from app import app
    
    with app.app_context():
        check_all_categories()
