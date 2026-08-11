"""Örnek (demo) veri üretimi.

Bu modüller daha önce tests/fixtures/ altındaydı ve routes/settings.py
üretim kodundan import ediyordu. Test paketi üretim bağımlılığı olmamalı;
bu yüzden infrastructure katmanına taşındılar. Test paketi de buradan
import eder.

Yeni mimari: DemoDataOrchestrator kullanılır.
Eski fonksiyonlar (generate_admin_demo_data, clear_admin_demo_data) 
backward compatibility için tutulmuştur ama deprecated'tır.
"""

from .demo_data_orchestrator import DemoDataOrchestrator, generate_advanced_demo_data

# Eski fonksiyonlar - backward compatibility için
from .admin_demo_data import clear_admin_demo_data, generate_admin_demo_data

__all__ = [
    "DemoDataOrchestrator",         # Yeni mimari sınıf
    "generate_advanced_demo_data",  # Yeni mimari fonksiyon - kullanın
    "clear_admin_demo_data",        # DEPRECATED - backward compatibility
    "generate_admin_demo_data",     # DEPRECATED - backward compatibility
]
