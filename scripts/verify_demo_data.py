"""
Demo Veri Doğrulama Scripti
Oluşturulan 3 yıllık transaction verilerini doğrular
"""

import sys
import os
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app
from models import Transaction

def verify_demo_data():
    """Demo veriyi doğrular"""
    
    with app.app_context():
        transactions = Transaction.query.filter_by(is_deleted=False).all()
        
        print(f"Toplam transaction: {len(transactions)}")
        
        # Kategori dağılımı
        categories = Counter([tx.category for tx in transactions])
        print("\nKategori dağılımı:")
        for cat, count in categories.most_common():
            print(f"  {cat}: {count}")
        
        # Yıl dağılımı
        years = Counter([tx.date[:4] for tx in transactions])
        print("\nYıl dağılımı:")
        for year, count in sorted(years.items()):
            print(f"  {year}: {count}")
        
        # Tip dağılımı
        types = Counter([tx.type for tx in transactions])
        print("\nTip dağılımı:")
        for tx_type, count in types.most_common():
            print(f"  {tx_type}: {count}")
        
        # Durum dağılımı
        statuses = Counter([tx.status for tx in transactions])
        print("\nDurum dağılımı:")
        for status, count in statuses.most_common():
            print(f"  {status}: {count}")

if __name__ == '__main__':
    verify_demo_data()
