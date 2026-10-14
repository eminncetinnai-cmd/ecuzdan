# E-Cüzdan — Domain Sözlüğü (Glossary)

> **AI Agent için:** Bu dosyayı oku. Bir terimi burada bulursan kaynak dosyaya gitme — bu sözlük yeterlidir.

---

## 🧩 Temel Domain Terimleri

| Terim | Türkçe Karşılığı | Kod Karşılığı | Açıklama |
|-------|-----------------|--------------|----------|
| **Tenant** | Kiracı / Hesap | `models.Tenant`, `tenant_id: str` | Multi-tenant mimarisinin temel birimi. Her kullanıcı bir tenant'a bağlıdır. `tenant_id` her DB sorgusunda filtre olarak kullanılmalıdır. |
| **User** | Kullanıcı | `models.User`, `user_id: int` | Sisteme giriş yapan kişi. Roller: `kullanici`, `tenant_admin`, `yonetici`, `sistem_yoneticisi`. |
| **Transaction** | İşlem | `models.Transaction` | Tek bir nakit hareketi. Tip: `Gelir`, `Gider`, `Yatırım`, `Transfer`. Durum: `Ödendi`, `Bekliyor`. |
| **RecurringPlan** | Düzenli Plan | `models.RecurringPlan` | Tekrarlayan gelir/gider şablonu. Her dönem için `Transaction` üretir. Tipler: `Taksit`, `Abonelik`, `DCA`, `Kira`. |
| **Asset** | Varlık | `models.Asset` | Kullanıcının sahip olduğu yatırım varlığı (altın, hisse, kripto, gayrimenkul). |
| **Category** | Kategori | `models.Category` | İşlem ve varlıkları gruplandıran etiket (örn: Gıda, Ulaşım, Teknoloji). |
| **Payment** | Ödeme | `models.Payment` | `RecurringPlan`'ın ödenmiş bir taksidini temsil eder. Borç hesabında düşülür. |
| **PlanOccurrence** | Plan Dönemi | `models.PlanOccurrence` | Bir planın tek bir beklenen dönemini ve yaşam döngüsünü temsil eder. Durum: `scheduled`, `paid`, `skipped`, `cancelled`. |
| **BankAccount** | Banka Hesabı | `models.BankAccount` | Kullanıcının banka/nakit hesabı. İşlemlere bağlanabilir. |
| **live** | Canlı Piyasa | `engines.financial_engine.get_live_data()` | Arka planda güncellenen USD, EUR, Altın fiyatları ve hava durumu. Tüm şablonlarda `{{ live.usd }}`, `{{ live.eur }}`, `{{ live.gold }}`, `{{ live.weather }}` ile erişilir. |
| **LedgerAdjustment** | Muhasebe Düzeltmesi | `models.LedgerAdjustment` | Ödenmiş işlemler için düzeltme/ters kayıt iş ve denetim kaydı. |

---

## 🔖 İşlem Sabitleri (`domain/transactions/constants.py`)

### İşlem Tipleri (`Transaction.type`)
| Sabit | Değer | Renk (UI) |
|-------|-------|-----------|
| `TRANSACTION_TYPE_INCOME` | `"Gelir"` | Emerald / `#10b981` |
| `TRANSACTION_TYPE_EXPENSE` | `"Gider"` | Rose / `#ef4444` |
| `TRANSACTION_TYPE_INVESTMENT` | `"Yatırım"` | Sky / `#0ea5e9` |
| `TRANSACTION_TYPE_TRANSFER` | `"Transfer"` | Slate / `#64748b` |

### İşlem Durumları (`Transaction.status`)
| Sabit | Değer |
|-------|-------|
| `TRANSACTION_STATUS_PAID` | `"Ödendi"` |
| `TRANSACTION_STATUS_PENDING` | `"Bekliyor"` |

### Kaynak Tipleri (`Transaction.source_type`)
| Sabit | Değer | Anlamı |
|-------|-------|--------|
| `SOURCE_TYPE_MANUAL` | `"manual"` | Kullanıcı elle girdi |
| `SOURCE_TYPE_PLAN` | `"plan"` | RecurringPlan'dan üretildi |
| `SOURCE_TYPE_ASSET` | `"asset"` | Varlık alımından oluştu |
| `SOURCE_TYPE_ASSET_SALE` | `"asset_sale"` | Varlık satışından oluştu |
| `SOURCE_TYPE_ADJUSTMENT` | `"adjustment"` | Muhasebe düzeltmesi |
| `SOURCE_TYPE_REVERSAL` | `"reversal"` | Ters kayıt |

---

## 💰 Para Birimi & Hassasiyet (`shared/currency_precision.py`)

| Varlık Tipi | Ondalık Basamak | Örnek |
|-------------|----------------|-------|
| Fiat (TRY, USD, EUR) | 2 | `1.234,56 ₺` |
| Kripto (BTC, ETH) | 8 | `0.00123456 ₿` |
| Altın (gram) | 3 | `2.500,500 g` |
| Altın (ons) | 4 | `2.500,5000 oz` |
| Hisse Senedi | 2 | `150,25 ₺` |
| Yatırım Fonu / ETF | 4 | `12,3456 ₺` |

### Semboller
| Kod | Sembol |
|-----|--------|
| TRY | ₺ |
| USD | $ |
| EUR | € |
| GBP | £ |
| BTC | ₿ |
| ETH | Ξ |
| GRAM | g |

---

## 👤 Kullanıcı Rolleri (`models.User.role`)

| Rol Değeri | Görünen Ad | Yetkiler |
|-----------|-----------|----------|
| `kullanici` | Kullanıcı | Kendi verileri |
| `tenant_admin` | Tenant Admin | Tenant verilerinin tamamı |
| `yonetici` | Yönetici | Admin paneli erişimi |
| `sistem_yoneticisi` | Sistem Yöneticisi | Tam platform erişimi |
| *(Super Admin)* | `emin` kullanıcısı | `SUPER_ADMIN_USERNAME` env'den gelir |

---

## 🏗️ Katman Terimleri (EAFGS)

| Terim | Katman | Açıklama |
|-------|--------|----------|
| **EAFGS** | — | Projenin mimari kısaltması: Engine, Application, Flask, Governance, Shared |
| **nakit_olay** | Ledger | `Transaction.ledger_layer` — nakit hareketi katmanı |
| **nakit_pozisyon** | Ledger | `RecurringPlan.ledger_layer` — plan/pozisyon katmanı |
| **flow_type** | RecurringPlan | Planın yönü: `Gelir` veya `Gider` |
| **tenant_id** | Tüm katmanlar | Her DB sorgusunda **zorunlu** filtre alanı |
| **source_type** | Transaction | İşlemin kökeni (manual, plan, asset, vb.) |

---

## 🌐 Context Processor (Tüm Şablonlarda Mevcut)

```python
# routes/__init__.py → register_context_processor() tarafından tüm şablonlara enjekte edilir
live                    # dict: {usd, eur, gold, weather, last_updated}
base_currency_code      # str: 'TRY'  (kullanıcı/tenant ayarına göre)
base_currency_symbol    # str: '₺'
current_user            # User modeli veya None
user_theme              # str: 'light' veya 'dark'
privacy_mode            # bool
date_str                # str: '1 Eylül 2026'
today_display           # str: '1 Eylül'
current_day             # str: 'Pazartesi'
current_time            # str: '08:15'
```

---

## ⚡ Piyasa Veri Sağlayıcı Zinciri

```
doviz.com (scrape)
    ↓ başarısız olursa
TCMB (XML API) — USD, EUR için resmi referans
    ↓ eksik alan varsa
Frankfurter ECB (JSON API) — USD/EUR/TRY hesaplama
    ↓ altın eksikse
GoldAPI.com (JSON API) — XAU/USD → TRY/gram dönüşümü
    ↓ hepsi başarısız olursa
yfinance — USDTRY=X, EURTRY=X, GC=F
```

Kaynak: `domain/analysis/services/fx_metals_provider.py`

---

*Son güncelleme: 2026-09-01*
