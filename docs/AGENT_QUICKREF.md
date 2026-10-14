# E-Cüzdan — AI Agent Hızlı Başvuru Kılavuzu

> Bu dosya, AI agent'ların token israfı yapmadan projeye hızlıca adapte olması için tutulur.
> **Yeni bir oturum başlarken bu dosyayı oku, sonra `AGENTS.md` ve ilgili kaynak dosyaya git.**

---

## 🚀 Sunucuyu Başlatma

```powershell
# Tek komutla başlat
.venv\Scripts\python.exe app.py

# Çalışıp çalışmadığını kontrol et
(Invoke-WebRequest -Uri "http://127.0.0.1:5000/login" -UseBasicParsing).StatusCode  # → 200 olmalı

# Eski procesi öldür ve yeniden başlat
Stop-Process -Name python, python3.13 -Force -ErrorAction SilentlyContinue
```

---

## ✅ Zorunlu Kalite Kapıları (Her değişiklikten önce çalıştır)

```powershell
# 1. Tasarım sistemi kontrolü — 0 ihlal olmalı
python scripts/check_design_system.py --ratchet

# 2. Birim testleri — hepsi geçmeli
python -m pytest tests/unit/ -q --no-cov

# 3. Mimari kapısı — 0 ihlal olmalı
powershell -ExecutionPolicy Bypass -File scripts/governance/run_architecture_gate.ps1 -Mode BLOCK

# 4. Statik tip kontrolü (Mypy) — 0 hata olmalı
python scripts/check_type_annotations.py
```

---

## 🪲 Bilinen Sorunlar & Çözümleri

### 1. Chart.js Sütunları Siyah Çıkıyor

**Sebep:** Canvas 2D context, CSS `var(--token)` değerlerini parse edemez.

**Çözüm:**
```javascript
function resolveColor(cssVar, fallback) {
  const val = getComputedStyle(document.documentElement).getPropertyValue(cssVar).trim();
  return val || fallback;
}
const CHART_COLORS = {
  income:     resolveColor('--color-emerald-500', '#10b981'),
  expense:    resolveColor('--color-rose-500',    '#ef4444'),
  investment: resolveColor('--color-sky-500',     '#0ea5e9'),
};
```

---

### 2. Makroda SVG/HTML Parametre Metin Olarak Çıkıyor

**Sebep:** Jinja2 otomatik HTML escape eder.

**Çözüm:** `templates/macros/buttons.html` dosyasında `{{ icon }}` → `{{ icon|safe }}`

---

### 3. Altın Fiyatı 20+ Ondalık Basamak Gösteriyor

**Sebep:** `Decimal.normalize()` ham hassasiyeti korur.

**Çözüm:** `_format_decimal(value, 'gold')` → `round(value, 2)` uygular.
Şablon tarafında: `{{ live.gold|format_ticker_price }}` filtresi 2 basamağa yuvarlar.

---

### 4. Şablon Değişiklikleri Tarayıcıda Görünmüyor

**Sebep:** Flask production modunda şablonları bellekte cache'ler.

**Çözüm:** `app.py`'de:
```python
app.config['TEMPLATES_AUTO_RELOAD'] = True
app.jinja_env.auto_reload = True
```
Ardından sunucuyu yeniden başlat.

---

### 5. Monitoring Sayfası Karanlık Tema Gösteriyor

**Sebep:** `monitoring.css`'deki `body:has(.monitoring-container)` global arka planı override eder.

**Çözüm:** `static/css/monitoring.css`'den dark body override'larını kaldır; `--obs-bg` token'larını `#ffffff / #e2e8f0` şeklinde tokenize et.

---

## 🎨 Standart Grafik Renkleri

| Kategori | Tailwind Token | Hex | Kullanım |
|----------|---------------|-----|----------|
| Gelir | `emerald-500` | `#10b981` | Gelir sütunları, pozitif değerler |
| Gider | `rose-500` | `#ef4444` | Gider sütunları, negatif değerler |
| Yatırım | `sky-500` | `#0ea5e9` | Yatırım sütunları |
| Genel/Plan | `indigo-500` | `#6366f1` | Plan, genel grafik serisi |
| Altın/Uyarı | `amber-500` | `#f59e0b` | Altın varlıkları, uyarılar |
| Borç | `orange-500` | `#f97316` | Borç, negatif plan |

---

## 💰 Para Birimi & Fiyat Formatı Kuralları

### Şablonda (Jinja2)
```jinja2
{# Para tutarı — format_money filtresi kullan #}
{{ amount|format_money }} {{ base_currency_symbol }}

{# Piyasa fiyatı (USD, EUR, Altın) — format_ticker_price filtresi kullan #}
{{ live.gold|format_ticker_price }} ₺

{# Para birimi sembolü #}
{{ a.currency|currency_symbol or base_currency_symbol }}
```

### JavaScript'te
```javascript
const symbol   = window.BASE_CURRENCY_SYMBOL || '₺';
const code     = window.BASE_CURRENCY_CODE   || 'TRY';

// Sayı formatlama (Türkçe binlik/ondalık)
function formatMoney(num) {
  return num.toLocaleString('tr-TR', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}
```

---

## 🗂️ Yeni Özellik Ekleme — Hızlı Kontrol Listesi

- [ ] **Domain katmanı** — iş mantığı (`domain/<alan>/services/`)
- [ ] **Repository** — DB sorgusu, `tenant_id` filtreli (`repositories/`)
- [ ] **Route** — blueprint handler (`routes/<özellik>.py`)
- [ ] **Template** — `{% extends "layout.html" %}`, makrolar kullan
- [ ] **Blueprint kayıt** — `app.py`'de `app.register_blueprint(...)`
- [ ] **Tasarım sistemi** — `check_design_system.py --ratchet` → 0 ihlal
- [ ] **Birim testleri** — `pytest tests/unit/ -q --no-cov` → tümü geçmeli
- [ ] **Mimari kapı** — `run_architecture_gate.ps1 -Mode BLOCK` → 0 ihlal

---

## 🧩 Makro Hızlı Referans

```jinja2
{% from "macros/buttons.html"  import button_primary, button_secondary, button_danger, button_success, button_gradient %}
{% from "macros/forms.html"    import form_input, form_select, form_textarea %}
{% from "macros/cards.html"    import kpi_card, alert_box %}
{% from "macros/ui.html"       import badge, progress_bar %}
{% from "macros/modals.html"   import modal_base %}
{% from "macros/tables.html"   import data_table %}
{% from "macros/charts.html"   import chart_canvas %}
```

### Buton Örnekleri
```jinja2
{{ button_primary(text="Kaydet", submit=True) }}
{{ button_secondary(text="Vazgeç", onclick="closeModal()") }}
{{ button_danger(text="Sil", onclick="confirmDelete()") }}
{{ button_success(text="Onayla", submit=True) }}
{{ button_gradient(text="Hızlı İşlem", url="/transactions", gradient="from-indigo-600 to-indigo-800") }}
```

---

## 🏛️ Mimari Kural Özeti

```
Domain      → Flask/DB YASAK
Application → Flask YASAK, sadece domain servislerini çağırır
Repository  → tenant_id filter ZORUNLU her sorguda
Routes      → Blueprint, @login_required, CSRF koruması
Templates   → layout.html extend, makro kullan, style="" YASAK
```

---

## 📁 Kritik Dosya Rotaları

```
Business Logic:   domain/<alan>/services/
DB Queries:       repositories/
HTTP Handlers:    routes/<özellik>.py
Jinja Filters:    routes/__init__.py → @app.template_filter(...)
Context Vars:     routes/__init__.py → register_context_processor()
Live Data:        infrastructure/background/background_service.py
FX Provider:      domain/analysis/services/fx_metals_provider.py
CSS Tokens:       static/css/design-tokens.css
Master Template:  templates/layout.html
Macros:           templates/macros/*.html
```

---

*Son güncelleme: 2026-09-01 — Oturum öğrenmeleri dahil edildi.*
