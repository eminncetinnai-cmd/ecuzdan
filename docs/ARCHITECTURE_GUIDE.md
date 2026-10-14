# 🏛️ E-Cüzdan Kurumsal Klasör ve Kod Mimarisi Rehberi (EAFGS)

Bu kılavuz, E-Cüzdan projesinin dünya standartlarında, okunabilir, sürdürülebilir ve kurumsal düzeyde (Enterprise Application Framework & Governance Standards - EAFGS) mimari yapısını, katman sınırlarını, klasör görev dağılımını ve geliştirme kurallarını açıklar.

---

## 🧭 1. Mimari Katmanlar ve Sorumluluk Haritası (EAFGS Layering)

Projede her dosya tek ve kesin bir mimari katmana aittir. Bağımlılıklar daima dış katmandan iç katmana doğru akar:

```text
┌─────────────────────────────────────────────────────────────────────────┐
│                      1. SUNUM KATMANI (PRESENTATION)                    │
│   routes/            : Flask Blueprint'leri, HTTP handler'lar           │
│   templates/         : Jinja2 HTML şablonları & UI Makroları            │
│   static/            : Tasarım sistemi CSS token'ları, JS bileşenleri   │
└────────────────────────────────────┬────────────────────────────────────┘
                                     │
┌────────────────────────────────────▼────────────────────────────────────┐
│                    2. UYGULAMA KATMANI (APPLICATION)                    │
│   application/       : Use Case'ler, iş akışı orkestrasyonu             │
│   application/dtos/  : DTO (Data Transfer Objects), girdi/çıktı tipleri │
│   application/ports/ : Dış servis arayüzleri ve port sözleşmeleri       │
└──────────────────┬──────────────────────────────────┬───────────────────┘
                   │                                  │
┌──────────────────▼──────────────────┐   ┌───────────▼───────────────────┐
│       3. ALAN KATMANI (DOMAIN)      │   │     4. REPOSİTORY KATMANI     │
│   domain/                           │   │   repositories/               │
│   - Saf iş mantığı, domain servisleri│   │   - DB sorguları & persistence│
│   - Domain entity & value object'ler│   │   - Tenant_id filtreleme      │
│   - Finansal kurallar ve invariant'lar│ │   - SQLAlchemy ORM soyutlaması│
└──────────────────┬──────────────────┘   └───────────┬───────────────────┘
                   │                                  │
                   └──────────────────┬───────────────┘
                                      │
┌─────────────────────────────────────▼───────────────────────────────────┐
│                  5. ALTYAPI VE MOTORLAR (INFRASTRUCTURE)                 │
│   infrastructure/    : Arka plan işçileri, dış API'lar, Outbox, Event Bus│
│   engines/           : Finansal hesaplama, analiz ve simülasyon motorları│
│   database/          : SQL migrasyonları, şema sürümleri, seed verileri │
└─────────────────────────────────────────────────────────────────────────┘
                                      ▲
                                      │
┌─────────────────────────────────────┴───────────────────────────────────┐
│                   6. ENİNE KESEN ARAÇLAR (CROSS-CUTTING)                 │
│   shared/            : Katmanlar arası saf araçlar (Money, Decimal, DB) │
│   utils/             : Web oturum, loglama, formatlama ve güvenlik      │
│   validators/        : HTTP istek doğrulama mantığı                      │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 📁 2. Dizin Görev Dağılımı ve Katman Kuralları

| Dizin | Rol ve Sorumluluk | İzin Verilenler | Kesinlikle Yasak Olanlar |
| :--- | :--- | :--- | :--- |
| **`domain/`** | Çekirdek iş mantığı, finansal algoritmalar, varlık kuralları | Saf Python, `shared.*`, domain modelleri | `flask`, `requests`, `sqlalchemy.orm`, HTML/UI |
| **`application/`** | Use case orkestrasyonu, yetki kontrolleri, DTO yönetimi | `domain.*`, `repositories.*`, `application.dtos.*`, `shared.*` | `flask.render_template`, doğrudan ham SQL |
| **`application/dtos/`** | Katmanlar arası veri transfer nesneleri (Payload DTOs) | `dataclass`, `typing`, `decimal.Decimal` | Veritabanı oturumu, UI kodu |
| **`infrastructure/`** | Dış API istemcileri (yfinance, TCMB: `infrastructure/market/`), background thread'ler | Dış SDK'lar, ağ bağlantıları, `shared.*` | `routes.*`, UI şablonları |
| **`repositories/`** | Veritabanı okuma/yazma soyutlaması | `models.*`, `shared.db`, `sqlalchemy.*` | `flask.*`, HTTP `request`/`response` nesneleri |
| **`routes/`** | HTTP rotaları, form işleme, şablon bağlama | `application.*`, `domain.*`, `utils.*`, Flask | Ağır finansal hesaplamalar, doğrudan ham SQL |
| **`templates/`** | Jinja2 HTML arayüzü (`layout.html` genişletir) | Jinja filtreleri, UI makroları (`macros/`) | Inline CSS (`style="..."`), hardcoded renkler |
| **`static/`** | CSS token'ları, Chart.js grafikleri, istemci JS | Tailwind sınıfları, CSS değişkenleri | İş mantığı ve hassas API anahtarları |
| **`engines/`** | Konsolide finansal hesaplama, analiz ve simülasyon | Saf Python, `shared.*`, pandas/numpy | Flask nesneleri, HTTP rotaları |
| **`shared/`** | Katmanlar arası saf tip ve yardımcılar | Para birimi hassasiyeti, `format_utils`, circuit breaker, db | Flask request bağlamı |
| **`utils/`** | Web ve oturum destek fonksiyonları | Flask oturumu, yetkilendirme, UI bileşenleri | Saf domain iş kuralları |
| **`database/`** | Şema migrasyonları, versiyon kontrolü, tohum veriler | Alembic/SQL script'leri, migration testleri | Web view fonksiyonları |
| **`config/`** | Çalışma zamanı YAML konfigürasyonları | `special_codes.yaml`, `demo_data/*.yaml` | Python bağımlılıkları |
| **`configuration/`**| Python paket bağımlılıkları ve lock dosyaları | `dependencies/requirements*.txt` | Uygulama çalışma zamanı verisi |
| **`governance/`** | Mimari kurallar, dosya politikaları | YAML politika tanımları, Markdown kılavuzları | Üretim uygulama kodu |
| **`scripts/`** | CI/CD, mimari kapılar, preflight testleri | Yönetişim ve otomasyon script'leri | Runtime web rotaları |
| **`tests/`** | Kapsamlı test piramidi (`unit`, `integration`, `regression`) | Pytest fixture'ları, test assertion'ları | Üretim kodunda test import'ları |

---

## 🔒 3. Kök Dizin (Root) Temizlik Standartları

Kök dizin (`/`), gereksiz geçici dosyalar ve test kırıntılarından kesinlikle arındırılmış olmalıdır. Yalnızca projenin çekirdek yapılandırma ve giriş noktalarına izin verilir:

### İzinli Kök Dosyalar:
- **Giriş Noktaları:** `app.py`, `wsgi.py`, `worker.py`
- **Konfigürasyon:** `config.py`, `.env.example`, `.env`, `requirements.txt`
- **Paketleme & Test:** `pyproject.toml`, `pytest.ini`, `mypy.ini`, `package.json`, `tailwind.config.js`
- **Yönetişim & Belgeler:** `README.md`, `AGENTS.md`, `.gitignore`
- **Uyumluluk Cepheleri:** `models.py`, `market_data_service.py`

> ⛔ **Yasak Kalıplar:** Kök dizinde `test_*.py`, `temp_*.py`, `fix*.py`, `debug*.py`, `*_v2.py`, `*_final.py` veya `*.tmp` dosyaları ASLA barındırılamaz.

---

## 🏢 4. Çoklu Kiracı (Multi-Tenant) İzolasyonu ve Veri Güvenliği

1. **Katı Kiracı Filtrelemesi:** Tüm veritabanı sorguları ve repository metotları istisnasız `tenant_id` filtresi içermek zorundadır:
   ```python
   # DOĞRU:
   Transaction.query.filter_by(tenant_id=current_user.tenant_id, is_deleted=False).all()
   
   # YANLIŞ (GÜVENLİK İHLALİ):
   Transaction.query.all()
   ```
2. **Kaskat Silme Güvenliği (Foreign Key Hierarchy):** İlişkisel silme işlemlerinde child (çocuk) kayıtlar parent (ebeveyn) kayıtlardan önce temizlenmelidir:
   $$\text{LedgerAuditEvent} \rightarrow \text{LedgerAdjustment} \rightarrow \text{PlanOccurrence} \rightarrow \text{Payment} \rightarrow \text{Transaction} \rightarrow \text{BankStatementSnapshot} \rightarrow \text{BankAccount} \rightarrow \text{Asset}$$
3. **Fail-Closed Güvenlik:** Yetkilendirme veya veri doğrulama hatalarında sistem daima güvenli duruma düşmeli (`rollback_session()`), genel hata mesajı döndürmeli ve denetim kaydı (`audit_log`) oluşturmalıdır.

---

## 🚀 5. Geliştirici İş Akışı ve Kalite Kapıları (Quality Gates)

Yeni bir özellik eklerken veya hata düzeltirken şu sıra izlenmelidir:
1. **Domain Servisi:** İş mantığı `domain/` katmanında Flask'sız yazılır.
2. **Repository:** Sorgu `repositories/` katmanında `tenant_id` ile yazılır.
3. **Application:** Use case `application/` katmanında orkestre edilir.
4. **Route:** HTTP handler `routes/` altında Blueprint'e bağlanır.
5. **Template & UI:** Arayüz Jinja2 makroları (`templates/macros/`) kullanılarak oluşturulur.
6. **Kalite Kapıları Doğrulaması:**
   ```powershell
   # 1. Tasarım sistemi tutarlılığı (0 ihlal)
   python scripts/check_design_system.py --ratchet

   # 2. Mimari kapı denetimi (BLOCK modu — 0 ihlal)
   powershell -ExecutionPolicy Bypass -File scripts/governance/run_architecture_gate.ps1 -Mode BLOCK

   # 3. Statik tip denetimi (Mypy — 0 hata)
   python scripts/check_type_annotations.py

   # 4. Master Pre-Flight Smoke Gate (0 template hatası, 0 HTTP 500)
   python scripts/preflight_check.py

   # 5. Birim ve entegrasyon testleri
   python -m pytest tests/unit/ -q --no-cov
   ```
