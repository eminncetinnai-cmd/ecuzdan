"""
Kategori Referans Kontrol Scripti
Kategorilerin hangi tablolarda referans edildiğini kontrol eder.
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models import Category, Transaction, RecurringPlan

def check_category_references():
    """Kategori referanslarını kontrol eder"""
    
    # Fazlı kategori kodları
    extra_codes = [
        'GLR-6009', 'GLR-6010', 'GLR-6011',
        'GDR-7010', 'GDR-7011', 'GDR-7012', 'GDR-7013', 'GDR-7014', 
        'GDR-7015', 'GDR-7016', 'GDR-7017', 'GDR-7018', 'GDR-7019', 'GDR-7020',
        'YTR-1008'
    ]
    
    for code in extra_codes:
        cat = Category.query.filter_by(code=code).first()
        if cat:
            print(f"\n{code} - {cat.name}:")
            
            # Transaction referansları
            tx_count = Transaction.query.filter_by(category=cat.name).count()
            if tx_count > 0:
                print(f"  ⚠️  {tx_count} işlem referansı var")
            else:
                print(f"  ✓ İşlem referansı yok")
            
            # RecurringPlan referansları
            plan_count = RecurringPlan.query.filter_by(category=cat.name).count()
            if plan_count > 0:
                print(f"  ⚠️  {plan_count} plan referansı var")
            else:
                print(f"  ✓ Plan referansı yok")
            
            # Diğer olası referanslar
            if tx_count == 0 and plan_count == 0:
                print(f"  ✅ Silinebilir")
        else:
            print(f"\n{code} - Bulunamadı")

if __name__ == '__main__':
    from app import app
    
    with app.app_context():
        print("Kategori referansları kontrol ediliyor...")
        check_category_references()
