"""
E-Cüzdan Domain Katmanı (Domain Layer) — Public API & Modül Haritası

Bu katman SAF İŞ MANTIĞI (Pure Business Logic) içerir.
KURAL: Bu katmanda Flask ('from flask import ...') ve SQLAlchemy db.Model
import etmek KESİNLİKLE YASAKTIR.

Domain Alt Modülleri ve Sorumlulukları:
  - transactions:   İşlem mantığı, nakit akışı analizi, durum sabitleri
  - ledger:         Muhasebe defteri (çift taraflı kayıt), bakiye tutarlılığı
  - analysis:       FX/altın sağlayıcı zinciri (fx_metals_provider), BIST, TEFAS
  - planning:       Düzenli plan dönemleri (occurrence_service), bütçeler
  - portfolio:      Varlık değerleme, portföy dağılımı ve ROI hesaplamaları
  - reconciliation: Banka ekstresi mutabakatı ve eşleştirme
  - categories:     Kategori yönetimi, varsayılan kategoriler
  - notifications:  Bildirim kuralları, uyarılar ve dağıtım
  - market:         Piyasa verileri iş mantığı
  - storage_health: Veritabanı sağlık kontrolü, temizlik ve arşivleme
  - tenant:         Kiracı (tenant) kuralları ve sınırları
  - users:          Kullanıcı rolleri, yetenekleri (capabilities) ve tercihleri
  - demo:           Demo veri üreticileri ve fabrikaları
  - ai:             Finansal içgörüler ve yapay zeka analiz servisleri
  - admin:          Yönetici güvenlik ve denetim kuralları
  - catalog:        Varlık/kategori katalogları
  - reporting:      Raporlama iş kuralları
  - common:         Ortak domain tipleri ve arayüzler
"""

__all__ = [
    "admin",
    "ai",
    "analysis",
    "catalog",
    "categories",
    "common",
    "demo",
    "ledger",
    "market",
    "notifications",
    "planning",
    "portfolio",
    "reconciliation",
    "reporting",
    "storage_health",
    "tenant",
    "transactions",
    "users",
]
