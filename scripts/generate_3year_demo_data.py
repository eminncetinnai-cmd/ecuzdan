"""
3 Yıllık Demo Veri Oluşturma Scripti
Standart kategorileri kullanarak 3 yıllık (2024, 2025, 2026) transaction verileri oluşturur
"""

import sys
import os
from datetime import datetime, timedelta
import random

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app, db
from models import Transaction, Category, Tenant

def generate_demo_data():
    """3 yıllık demo veri oluşturur"""
    
    with app.app_context():
        # Default tenant'ı al
        default_tenant = Tenant.query.filter_by(id='default').first()
        if not default_tenant:
            print("❌ Default tenant bulunamadı!")
            return
        
        # Mevcut kategorileri al
        categories = Category.query.filter_by(tenant_id=None).all()
        category_map = {cat.name: cat for cat in categories}
        
        # Kategori isimleri
        income_categories = [
            'Maaş / Ücret Geliri', 'Avans', 'Ek Gelir / Diğer Gelirler', 
            'Faiz Geliri', 'Kira Geliri', 'Prim & İkramiye', 
            'Yardım & Destek', 'Yatırım Kazancı'
        ]
        
        expense_categories = [
            'Kredi Kartı Ödemesi', 'Kredi Ödemeleri', 'Aylık Sabit Gider', 
            'Bağış & Yardım', 'Eğitim & Kurslar', 'Kira', 
            'Kişisel Bakım', 'Nafaka', 'Diğer Giderler'
        ]
        
        investment_categories = [
            'Altın Alımı', 'Diğer Yatırımlar', 'Fon', 
            'Gayrimenkul', 'Hisse Senedi', 'Kripto', 'Nakit & Mevduat'
        ]
        
        transfer_categories = ['Transfer']
        
        # 3 yıllık veri oluştur (2024, 2025, 2026)
        years = [2024, 2025, 2026]
        
        total_transactions = 0
        
        for year in years:
            print(f"\n{year} yılı için transaction'lar oluşturuluyor...")
            
            for month in range(1, 13):
                # Her ay için rastgele transaction'lar oluştur
                num_transactions = random.randint(15, 25)
                
                for _ in range(num_transactions):
                    # Rastgele bir tarih seç
                    day = random.randint(1, 28)
                    date = f"{year}-{month:02d}-{day:02d}"
                    
                    # Transaction tipi seç
                    rand = random.random()
                    
                    if rand < 0.35:  # %35 Gelir
                        category_name = random.choice(income_categories)
                        tx_type = 'Gelir'
                        amount = random.randint(5000, 25000)
                        status = random.choice(['Ödendi', 'Ödendi', 'Ödendi', 'Bekliyor'])
                    elif rand < 0.75:  # %40 Gider
                        category_name = random.choice(expense_categories)
                        tx_type = 'Gider'
                        amount = random.randint(500, 8000)
                        status = random.choice(['Ödendi', 'Ödendi', 'Ödendi', 'Bekliyor'])
                    elif rand < 0.90:  # %15 Yatırım
                        category_name = random.choice(investment_categories)
                        tx_type = 'Yatırım'
                        amount = random.randint(1000, 15000)
                        status = random.choice(['Ödendi', 'Ödendi', 'Bekliyor'])
                    else:  # %10 Transfer
                        category_name = random.choice(transfer_categories)
                        tx_type = 'Transfer'
                        amount = random.randint(1000, 5000)
                        status = 'Ödendi'
                    
                    # Transaction oluştur
                    transaction = Transaction(
                        date=date,
                        type=tx_type,
                        category=category_name,
                        amount=amount,
                        status=status,
                        description=f"{category_name} - {year}-{month:02d}",
                        tenant_id=default_tenant.id,
                        is_deleted=False
                    )
                    
                    db.session.add(transaction)
                    total_transactions += 1
        
        try:
            db.session.commit()
            print(f"\n✅ {total_transactions} transaction başarıyla oluşturuldu!")
            print(f"   Yıllar: {years}")
            print(f"   Ortalama ay başına: {total_transactions / (len(years) * 12):.1f} transaction")
        except Exception as e:
            db.session.rollback()
            print(f"\n❌ Hata oluştu: {e}")
            raise

if __name__ == '__main__':
    generate_demo_data()
