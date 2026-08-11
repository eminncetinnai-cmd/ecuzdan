"""
Demo veri test scripti
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app import app
from infrastructure.demo import clear_admin_demo_data, generate_advanced_demo_data

with app.app_context():
    print("Mevcut demo verileri temizleniyor...")
    clear_admin_demo_data()
    print("Demo verileri oluşturuluyor...")
    generate_advanced_demo_data(start_year=2025, end_year=2027)
    print("Demo veri testi tamamlandı!")
