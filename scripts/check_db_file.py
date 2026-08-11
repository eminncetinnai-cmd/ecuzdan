"""
Veritabanı Dosyası Kontrol Scripti
SQLite dosyasını doğrudan kontrol eder.
"""

import sqlite3
import os

# Veritabanı dosyası yollarını kontrol et
possible_paths = [
    os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'instance', 'e_cuzdan.db'),
    os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'e_cuzdan.db'),
    os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'instance', 'app.db'),
]

db_path = None
for path in possible_paths:
    if os.path.exists(path):
        db_path = path
        print(f"Veritabanı dosyası bulundu: {db_path}")
        break

if not db_path:
    print("Veritabanı dosyası bulunamadı!")
    exit(1)

def check_db_file():
    """SQLite dosyasını doğrudan kontrol eder"""
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Tablo yapısını kontrol et
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        print(f"\nTablolar: {[t[0] for t in tables]}")
        
        # Kategori tablosunu kontrol et
        cursor.execute("SELECT COUNT(*) FROM category WHERE tenant_id IS NULL")
        total_count = cursor.fetchone()[0]
        print(f"\nToplam sistem genelinde kategori: {total_count}")
        
        # Standart kategorileri kontrol et
        standard_codes = [
            'GLR-6001', 'GLR-6002', 'GLR-6003', 'GLR-6004', 'GLR-6005',
            'GLR-6006', 'GLR-6007', 'GLR-6008',
            'GDR-7001', 'GDR-7002', 'GDR-7003', 'GDR-7004', 'GDR-7005',
            'GDR-7006', 'GDR-7007', 'GDR-7008', 'GDR-7009',
            'YTR-1001', 'YTR-1002', 'YTR-1003', 'YTR-1004', 'YTR-1005',
            'YTR-1006', 'YTR-1007'
        ]
        
        print(f"\nStandart kategori kontrolü:")
        for code in standard_codes:
            cursor.execute("SELECT name FROM category WHERE code = ? AND tenant_id IS NULL", (code,))
            result = cursor.fetchone()
            if result:
                print(f"  ✓ {code} - {result[0]}")
            else:
                print(f"  ✗ {code} - BULUNAMADI")
        
        # Fazlı kategorileri bul
        placeholders = ','.join(['?'] * len(standard_codes))
        cursor.execute(f"SELECT code, name FROM category WHERE tenant_id IS NULL AND code NOT IN ({placeholders})", standard_codes)
        extra_categories = cursor.fetchall()
        
        if extra_categories:
            print(f"\nFazlı kategoriler: {len(extra_categories)}")
            for code, name in extra_categories:
                print(f"  - {code or 'N/A'} - {name}")
        else:
            print(f"\n✅ Fazlı kategori yok!")
        
        conn.close()
        
    except Exception as e:
        print(f"Hata: {e}")

if __name__ == '__main__':
    check_db_file()
