# E-Cüzdan Mimari ve Dosya Yönetişimi Kılavuzu (EAFGS)

## 1. Mimari Katmanlar ve Sorumluluk Haritası

E-Cüzdan projesinde her dosya tek ve net bir mimari katmana aittir:

```text
┌─────────────────────────────────────────────────────────────────────────┐
│                           ROUTES (HTTP LAYER)                           │
│   Flask Blueprints, View Functions, Auth Boundary, Request Validation   │
└────────────────────────────────────┬────────────────────────────────────┘
                                     │
┌────────────────────────────────────▼────────────────────────────────────┐
│                       APPLICATION (USE CASE LAYER)                      │
│      Application Services, Use Cases, Workflow Orchestration, Ports     │
└──────────────────┬──────────────────────────────────┬───────────────────┘
                   │                                  │
┌──────────────────▼──────────────────┐   ┌───────────▼───────────────────┐
│        DOMAIN (CORE BUSINESS)       │   │        REPOSITORIES           │
│ Entities, Value Objects, Rules,     │   │ Data Access Abstraction,      │
│ Financial Calculation Services      │   │ SQLAlchemy Queries, Mapping   │
└─────────────────────────────────────┘   └───────────┬───────────────────┘
                                                      │
┌─────────────────────────────────────────────────────▼───────────────────┐
│                        INFRASTRUCTURE & DATABASE                        │
│   External APIs, Market Feeds, Redis, OTel, Database Models & Migrations│
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Katmanlar ve İzin Verilen / Yasaklanan Bağımlılıklar

| Katman | Konum | İzin Verilen Bağımlılıklar | Kesinlikle Yasak Olanlar |
|---|---|---|---|
| **Domain** | `domain/` | Saf Python, `shared.*`, domain entities/services | `flask`, `routes.*`, `infrastructure.*`, UI, HTML |
| **Application** | `application/` | `domain.*`, `repositories.*`, `ports.*`, `utils.*` | `flask.render_template`, route view fonksiyonları |
| **Routes** | `routes/` | `application.*`, `domain.*`, `utils.*`, `bootstrap.*` | Ağır finansal hesaplamalar, doğrudan ham SQL |
| **Repositories**| `repositories/` | `models.*`, `database.*`, `sqlalchemy.*`, `domain.*` | `flask.*`, HTTP istek/yanıt nesneleri |
| **Infrastructure**| `infrastructure/`| Dış servis SDK'ları, `utils.*`, `shared.*` | `routes.*` |
| **Governance** | `governance/` | YAML/JSON kural tanımları, policy dosyaları | Üretim kodu |
| **Workspace** | `.work/` | Geçici probe, test ve inceleme script'leri | Doğrudan production import'ları |

---

## 3. Yaşam Döngüsü ve "Promote or Purge" Protokolü

Tüm geçici geliştirme ve inceleme dosyaları öncelikle `.work/` dizininde açılır:
* `.work/investigations/` — Hata ve kök neden analizleri
* `.work/experiments/` — Yeni kütüphane veya mimari denemeleri
* `.work/probes/` — Geçici veri veya ağ testleri
* `.work/generated/` — Otomatik üretilen geçici veriler
* `.work/sessions/` — AI oturum notları ve logları

**Promote Kararı:** Geçici dosya kalıcı bir fayda sağlıyorsa:
1. `infrastructure/` veya `scripts/` altına taşınır.
2. Naming kurallarına göre yeniden adlandırılır.
3. Birim testleri `tests/` altına eklenir.
4. `.work/` kopyası temizlenir.

---

## 4. İsimlendirme Kuralları

| Dosya Türü | Standart | Yasaklı Kalıplar |
|---|---|---|
| Python Modülleri | `snake_case.py` | `*_final.py`, `*_v2.py`, `*_old.py`, `*_backup.py` |
| Şablonlar | `snake_case.html` | `*_new.html`, `*_temp.html` |
| Testler | `test_*.py` (yalnızca `tests/` altında) | Kök dizinde veya domain içinde test dosyaları |
| Scriptler | `snake_case.py` (yalnızca `scripts/` altında) | `fix.py`, `debug.py`, `run.py` (kök dizinde) |

---

## 5. Domain Katmanı İyileştirme Yol Haritası (Remediation Roadmap)

Mevcut 13 legacy domain dosyasında bulunan `flask` import'ları (`g`, `current_app`), kademeli olarak aşağıdaki şekilde arındırılacaktır:
1. **Tenant & User Context:** `flask.g` doğrudan domain içinde okunmak yerine, servis metodlarına parametre (`tenant_id: int`) olarak geçilecek veya `shared/context.py` sağlayıcısı üzerinden enjekte edilecek.
2. **Logging:** `current_app.logger` yerine `utils.logging_config.get_logger(__name__)` kullanılacak.
3. **Purity Kontrolü:** İyileştirme tamamlandıkça `architecture_gate.py` `BLOCK` seviyesine çekilerek mimari aşınma tamamen engellenecektir.
