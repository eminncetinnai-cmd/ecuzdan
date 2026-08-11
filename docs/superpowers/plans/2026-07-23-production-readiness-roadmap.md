# E-Cüzdan v15 — Localhost Production-Readiness Roadmap

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Bring E-Cüzdan v15 from "half-migrated, undocumented-drift" state to a version that can be run on localhost in a production-equivalent configuration (Postgres, rate limiting active, no cross-tenant leaks, no Decimal/float crashes) and used for real testing before an actual remote deployment.

**Architecture:** No architectural rewrite. The Clean Architecture layering (`domain`/`application`/`infrastructure`/`repositories`/`routes`) and the `TenantScopedRepository` primitive already in `repositories/base.py` are correct and stay as-is. This plan closes gaps *within* that architecture: a pinned environment, two live crash/leak bugs, the remaining unscoped repository methods, production hardening config, and CI guardrails.

**Tech Stack:** Python 3.10–3.12 (see Task 0.1 for why not 3.14), Flask + Flask-SQLAlchemy, SQLite (dev) → PostgreSQL (local docker for prod-parity testing), pytest, ruff, import-linter, flask-limiter.

## Global Constraints

- Windows machine, PowerShell primary shell, Bash tool also available — every command below is given for both where behavior differs.
- No destructive git operations without explicit user confirmation (repo is not yet under version control — Task 0.0 creates it).
- No new abstractions beyond what a task needs — reuse `TenantScopedRepository`/`require_tenant_id()` (already exist in `repositories/base.py`), do not invent a second tenant-scoping mechanism.
- Every "fix a leak/crash" task starts with a failing test that reproduces the real bug against the real code — not a hypothetical.
- Currency/ledger fields (`Transaction.amount`, `Asset.value`, etc.) must stay `Decimal` end-to-end. Analytics/statistical code (Monte Carlo, risk scores) is explicitly allowed to convert to `float` at its entry boundary — this is intentional, not a regression (confirmed against SPRINT-01's own 170x Decimal-slowdown benchmark).

---

## ⚠️ Doğrulanmış Kök Nedenler (varsayım değil — kodda ve loglarda doğrulandı)

Bunlar hipotez değil; `logs/e_cuzdan.log`, gerçek kod okuma ve `pip list` ile doğrulandı:

| # | Belirti | Kök Neden | Kanıt |
|---|---------|-----------|-------|
| H1 | `ruff`/`lint-imports` çalıştırılamıyor; flask-limiter bazı çalıştırmalarda aktif, bazılarında değil | Proje için **izole bir venv yok**; `python`/`pip` bu makinedeki tamamen ilgisiz global bir kuruluma (`edge-tts`, `faster-whisper` gibi başka bir projeye ait paketler) çözümleniyor | `pip list` çıktısı: flask/pandas/ruff/import-linter hiçbiri yok, ama proje çalışıyor → farklı bir Python birleşimi kullanılıyor. `python --version` → 3.14.6, ama `pyproject.toml` `target-version='py310'` |
| H2 | `logs/e_cuzdan.log`: `WARNING flask-limiter yüklü değil; rate limiting devre dışı.` (19:37 kaydı) — ama 17:24 kaydında `Flask-Limiter aktif (memory storage).` | `app.py`'de flask-limiter entegrasyonu **gerçek ve doğru yazılmış** (satır 78-125); ama `requirements.txt`'te flask-limiter **hiç yok**. Bu yüzden hangi ortamda çalıştırıldığına göre login brute-force koruması sessizce devre dışı kalıyor | `grep -in limiter requirements.txt` → boş sonuç |
| H3 | `pyproject.toml`'daki `[tool.ruff]` ve `[tool.importlinter]` hiçbir yerde icra edilemiyor | `ruff` ve `import-linter` de `requirements.txt`'te yok; ayrı bir dev-requirements dosyası da yok | Aynı grep, `ruff`/`import-linter` için de boş |
| H4 | `/strategy` sayfası her zaman 500 veriyor: `ERROR routes.strategy: Strategy page error: unsupported operand type(s) for *: 'decimal.Decimal' and 'float'` | SPRINT-01 Decimal migrasyonu `Asset.value/quantity/purchase_cost`, `Transaction.amount`, `StrategySettings.*` alanlarını `Numeric(19,4)`'e taşıdı (SQLAlchemy bunu Python `Decimal` olarak döndürür). `domain/analysis/services/strategy_engine.py` bu Decimal değerleri hâlâ ham `float` sabitleriyle (`0.40`, senaryo sözlükleri, `macro_data.get(...)/100`) karıştırıyor. En kesin çakışma noktası: `calculate_real_yields()` satır 253 — `nominal_roi` (artık `Asset.roi` property'sinden Decimal) `cum_inflation` (macro API başarılı olduğunda float) ile bölünüyor → **kalıcı satın alma maliyeti olan her varlıkta garantili çökme**. İkinci nokta: `_run_single_scenario_sim()` satır 60/63, `StrategySettings` alanları null değilse aynı sınıftan çakışma | Kod okuması: `domain/portfolio/models/portfolio_models.py:150-171` (`roi` property Decimal döndürüyor), `domain/analysis/services/strategy_engine.py:207-253` |
| H5 | `tenant_phase1_gap_inventory.md` çoğu iddiasında **güncelliğini yitirmiş** — `financial_repository.get_transaction/update_transaction/delete_transaction/transaction_page` zaten `_resolve_tenant_id()` ile korunuyor (satır 13-131). Ama **gerçek, hâlâ yaşayan** bir sızıntı var: `financial_repository.list_transactions()` (satır 35-40) tek metod olarak `_resolve_tenant_id()` çağırmıyor, `tenant_id` verilmezse **tüm tenant'ların** işlemlerini döndürüyor | `domain/planning/services/plan_service.py` satır 71 ve 97, `list_transactions(order_desc=False)`'ı **tenant_id vermeden** çağırıyor — bu da `/payment_calendar` sayfasındaki "bugünkü nakit" rakamını ve `/monthly_dashboard`'daki günlük bakiye grafiğini **tüm tenant'ların toplamından** hesaplıyor | Kod okuması: `repositories/financial_repository.py:35-40` + `domain/planning/services/plan_service.py:71,97` — canlı, tetiklenebilir, varsayımsal değil |

H4 ve H5, "test için localhost'ta canlıya alma" hedefini doğrudan engelliyor (bir sayfa her zaman 500 veriyor; bir diğeri yanlış veri gösteriyor) — bu yüzden **Phase 0**'a alındılar, tenant-güvenlik fazının geri kalanından önce.

---

## Faz Haritası

| Faz | Kapsam | Durum |
|-----|--------|-------|
| **Phase 0** | Ortam pinleme + H2/H3/H4/H5 hotfix'leri | Bu dokümanda tam detaylı |
| **Phase 1** | Kalan gerçek tenant açıkları (stale doküman elendikten sonra) | Bu dokümanda tam detaylı (tek gerçek P0: `portfolio_repository` unscoped asset metodları) |
| **Phase 2** | Decimal/float sınırının geri kalan motorlarda (financial_engine, simulation_runner, diğer domain/analysis servisleri) kapatılması | Ayrı plan — Phase 0'daki `_as_float` deseni tekrar kullanılacak |
| **Phase 3** | `app/` iskeletinin kaderi (sil ya da hedef mimari ilan et) + `application/transaction` vs `application/transactions` birleştirme | Ayrı plan |
| **Phase 4** | Localhost'ta prod-parity: docker-compose Postgres, health check, PII'siz log, session/rate-limit sertleştirme | Ayrı plan |
| **Phase 5** | Otomasyon guardrail'leri (önceki turda onaylanan hook/subagent'lar) | Kullanıcı onayı bekleniyor — ayrı adım |
| **Phase 6** | Localhost go-live smoke-test checklist | Phase 0-4 bitince yazılacak |

Her faz kendi başına test edilebilir, çalışan bir sonuç üretir (writing-plans skill'inin "Scope Check" kuralı gereği ayrıştırıldı). Şimdi Phase 0 ve Phase 1'i tam detayıyla veriyorum; Phase 2-4 bu plan onaylandıktan/uygulandıktan sonra aynı derinlikte ayrı dokümanlar olarak yazılacak.

---

# PHASE 0 — Ortam Pinleme + Doğrulanmış Hotfix'ler

### Task 0.0: Git deposu kur (güvenlik ağı)

Proje şu an git repository değil — hiçbir değişiklik geri alınamaz. Bu, sonraki her adımın önkoşulu.

**Files:**
- Create: `.gitignore` (genişlet — mevcut yoksa oluştur)
- Create: git repository (`.git/`)

- [ ] **Step 1: .gitignore içeriğini doğrula/genişlet**

`.gitignore` dosyasını oku; aşağıdakiler eksikse ekle:

```gitignore
__pycache__/
*.pyc
.venv/
venv/
*.db
*.db-shm
*.db-wal
.env
instance/
logs/*.log
htmlcov/
.coverage
staging/staging.db
staging/backups/
staging/backup/
```

- [ ] **Step 2: git init ve ilk commit**

```bash
cd "C:\Users\tl_yi\OneDrive\Masaüstü\ecuzdan\ecuzdan"
git init
git add -A
git status
```

Beklenen: `.env`, `*.db`, `logs/*.log`, `.venv/` çalışma listesinde **görünmemeli**. Görünüyorsa `.gitignore`'a dönüp düzelt, `git add` etme.

- [ ] **Step 3: İlk commit**

```bash
git commit -m "chore: initial commit baseline before production-readiness work"
git log --oneline -1
```

---

### Task 0.1: İzole venv + eksik bağımlılıkların kök nedenini kapat (H1, H2, H3)

**Files:**
- Create: `.venv/` (proje köküne)
- Modify: `requirements.txt`
- Create: `requirements-dev.txt`
- Modify: `E-CUZDAN_BASLAT.bat`

**Interfaces:**
- Produces: `.venv\Scripts\python.exe` — Task 0.2/0.3'teki testler ve tüm sonraki fazlar bu interpreter'ı kullanacak.

- [ ] **Step 1: Python 3.10–3.12 aralığında bir sürüm bul**

```powershell
py -0
```

Çıktıda `3.12`, `3.11` veya `3.10` varsa onu kullan (aşağıda `py -3.12` örnek). 3.14 dışında hiçbiri yoksa, `numpy`/`pandas`/`scipy`/`yfinance` kurulumunun başarılı olup olmadığını Step 3'te doğrula; başarısız olursa 3.12 kurulumu gerekecek — bu durumda dur ve kullanıcıya bildir (yeni Python kurulumu onay gerektirir).

- [ ] **Step 2: Proje köküne izole venv oluştur**

```powershell
cd "C:\Users\tl_yi\OneDrive\Masaüstü\ecuzdan\ecuzdan"
py -3.12 -m venv .venv
.venv\Scripts\python.exe -m pip install --upgrade pip
```

- [ ] **Step 3: requirements.txt'e eksik bağımlılıkları ekle**

`requirements.txt`'in sonuna ekle (mevcut dosyanın hiçbir satırı pinlenmemiş — aynı üslup korunuyor):

```
flask-limiter
```

- [ ] **Step 4: requirements-dev.txt oluştur (yeni dosya)**

```
-r requirements.txt
ruff
import-linter
```

- [ ] **Step 5: Kurulumu doğrula**

```powershell
.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.venv\Scripts\python.exe -c "import flask, flask_sqlalchemy, pandas, yfinance, flask_limiter; print('OK')"
```

Beklenen çıktı: `OK`. Hata varsa (örn. pandas 3.14/3.12 uyumsuzluğu) burada dur, hatayı raporla — varsayımsal bir "muhtemelen çalışır" ile geçme.

- [ ] **Step 6: ruff ve import-linter artık çalışıyor mu doğrula**

```powershell
.venv\Scripts\python.exe -m ruff check . --statistics
.venv\Scripts\python.exe -m lint_imports
```

Beklenen: `lint_imports` **PASS** basmalı (pyproject.toml'daki sözleşmeler zaten koda uygun yazılmıştı — bu sadece aracın artık çalışabildiğini kanıtlıyor). `ruff` bazı stil uyarıları basabilir; bunları bu task'ta düzeltme, sadece "artık çalışıyor" olduğunu doğrula.

- [ ] **Step 7: E-CUZDAN_BASLAT.bat'ı .venv kullanacak şekilde güncelle**

`E-CUZDAN_BASLAT.bat` içinde global `python` çağrılarını `.venv\Scripts\python.exe` ile değiştir. Dosyanın `[3/6]` ve `[4/6]` ve `[6/6]` bloklarını şu şekilde değiştir:

Eskisi (satır 16-17, 39-40, 50, 73):
```bat
python --version >nul 2>&1
...
python -m pip install -r requirements.txt
...
python -m pip install yfinance scipy pandas numpy
...
start "E-CUZDAN SUNUCUSU" cmd /k "cd /d "%~dp0" && python app.py"
```

Yenisi — dosyanın başına venv oluşturma adımı ekle, sonra tüm `python` çağrılarını `.venv\Scripts\python.exe` yap:

```bat
REM Venv kontrol et / olustur
echo [0/6] Sanal ortam kontrol ediliyor...
if not exist ".venv\Scripts\python.exe" (
    echo [+] .venv bulunamadi, olusturuluyor...
    py -3.12 -m venv .venv
)
set "PYEXE=.venv\Scripts\python.exe"
```

Ardından dosyadaki her `python --version`, `python -m pip install ...`, `python app.py` çağrısını `%PYEXE%` ile değiştir (satır 17, 40, 50, 73).

- [ ] **Step 8: Commit**

```bash
git add requirements.txt requirements-dev.txt E-CUZDAN_BASLAT.bat .gitignore
git commit -m "chore: pin isolated venv, add flask-limiter + dev tooling to declared deps"
```

`.venv/` commit edilmemeli (gitignore'da zaten var) — `git status` ile doğrula.

---

### Task 0.2: Hotfix — `/strategy` sayfası her zaman 500 veriyor (H4)

**Files:**
- Modify: `domain/analysis/services/strategy_engine.py`
- Test: `tests/test_strategy_engine_regression.py`

**Interfaces:**
- Consumes: `Asset.roi` (property, `domain/portfolio/models/portfolio_models.py:150`) — artık `Decimal` döndürüyor.
- Produces: `StrategyEngine.calculate_real_yields(assets)` — artık hem Decimal hem float girdilerle çökmeden çalışır, dönüş tipleri değişmez (hâlâ `dict`).

- [ ] **Step 1: Kök nedeni doğrulayan başarısız testi yaz**

`tests/test_strategy_engine_regression.py` dosyasının sonuna ekle (dosya yoksa oluştur, üstüne `from models import db` ve gerekli importları koy — aşağıdaki blok bağımsız çalışacak şekilde yazıldı):

```python
from decimal import Decimal

from models import AssetSector, Tenant, db


def test_calculate_real_yields_does_not_crash_on_decimal_asset(app):
    """SPRINT-01 Decimal migrasyonu sonrası Asset.value/roi artık Decimal.
    calculate_real_yields bunu float ile karistirip TypeError firlatmamali.
    Regression for: ERROR routes.strategy 'unsupported operand type(s) for *:
    decimal.Decimal and float'
    """
    from domain.analysis.services.strategy_engine import StrategyEngine
    from domain.portfolio.models.portfolio_models import Asset

    tenant = Tenant.query.filter_by(id='default').first()
    sector = AssetSector.query.filter_by(name='Teknoloji').first()

    asset = Asset(
        type='Hisse Senedi',
        name='Test Hissesi',
        value=Decimal('15000.0000'),
        purchase_date='2024-01-15',
        purchase_cost=Decimal('10000.0000'),
        quantity=Decimal('100.0000'),
        unit_price=Decimal('150.0000'),
        currency='TRY',
        symbol='TST',
        risk_level='Orta',
        liquidity='Likit',
        sector_id=sector.id,
        tenant_id=tenant.id,
    )
    db.session.add(asset)
    db.session.commit()

    engine = StrategyEngine.__new__(StrategyEngine)
    from models import StrategySettings
    engine.settings = StrategySettings(user_id=1, annual_inflation=Decimal('0.4000'))

    result = engine.calculate_real_yields([asset])

    assert 'assets' in result
    assert len(result['assets']) == 1
    assert isinstance(result['assets'][0]['real_roi'], float)
```

- [ ] **Step 2: Testi çalıştır, çöktüğünü doğrula**

```powershell
.venv\Scripts\python.exe -m pytest tests/test_strategy_engine_regression.py::test_calculate_real_yields_does_not_crash_on_decimal_asset -v
```

Beklenen: **FAIL** — `TypeError: unsupported operand type(s) for /: 'decimal.Decimal' and 'float'` (macro veri çekme testte muhtemelen başarısız olacağı için `except` bloğuna düşüp `self.settings.annual_inflation` — burada Decimal — kullanılacak, satır 247'deki `** years_held` (float) adımında patlayacak; macro veri başarılı olursa satır 253'te patlar — ikisi de aynı kök nedenin farklı tetikleyicisi).

- [ ] **Step 3: Decimal→float sınırını `calculate_real_yields` girişine koy**

`domain/analysis/services/strategy_engine.py` içinde `calculate_real_yields` metodunu değiştir. Mevcut (satır 207-219):

```python
    def calculate_real_yields(self, assets):
        """Reel getiri hesapla (dinamik enflasyon ile finans uzmanı mantığı)"""
        # Dinamik makroekonomik verileri çek
        try:
            from market_data_service import get_macro_economic_data
            macro_data = get_macro_economic_data()
            annual_inflation = macro_data.get('inflation_rate', 40.0) / 100
            policy_rate = macro_data.get('interest_rate', 37.0) / 100
        except Exception as e:
            logger.warning(f"Makro veri çekilemedi, varsayılan değerler kullanılıyor: {e}")
            annual_inflation = self.settings.annual_inflation or 0.40
            policy_rate = 0.37
```

Yeni:

```python
    def calculate_real_yields(self, assets):
        """Reel getiri hesapla (dinamik enflasyon ile finans uzmanı mantığı).

        Bu motor istatistiksel/analitik bir hesaplama katmanıdır, muhasebe
        defteri değildir — bu yüzden Decimal alanlar (Asset.value, Asset.roi)
        buraya girer girmez float'a çevrilir. Decimal hassasiyeti ledger
        katmaninda (financial_ledger.py) korunmaya devam eder.
        """
        # Dinamik makroekonomik verileri çek
        try:
            from market_data_service import get_macro_economic_data
            macro_data = get_macro_economic_data()
            annual_inflation = float(macro_data.get('inflation_rate', 40.0)) / 100
            policy_rate = float(macro_data.get('interest_rate', 37.0)) / 100
        except Exception as e:
            logger.warning(f"Makro veri çekilemedi, varsayılan değerler kullanılıyor: {e}")
            annual_inflation = float(self.settings.annual_inflation or 0.40)
            policy_rate = 0.37
```

- [ ] **Step 4: Per-asset döngüsünde Decimal alanları sınırda float'a çevir**

Aynı metodun döngü başlangıcını (satır 229-250 civarı) değiştir. Mevcut:

```python
        for a in assets:
            if not a.purchase_date:
                continue
```

Yeni — döngü gövdesinin en başına iki satır ekle:

```python
        for a in assets:
            if not a.purchase_date:
                continue

            asset_value = float(a.value)
            nominal_roi = float(a.roi) / 100
```

Sonra metodun geri kalanında `a.value` kullanılan her yeri `asset_value`, `a.roi / 100` kullanılan satırı (satır 250: `nominal_roi = a.roi / 100`) `nominal_roi` değişkeniyle değiştir — o satırı **sil** (artık döngü başında hesaplanıyor). `portfolio_metrics` bloğundaki (satır 276-278):

```python
            portfolio_metrics['total_nominal_value'] += a.value
            portfolio_metrics['total_real_value'] += a.value * (1 + real_roi)
            portfolio_metrics['inflation_burn'] += a.value * cum_inflation
```

şu şekilde değiştir:

```python
            portfolio_metrics['total_nominal_value'] += asset_value
            portfolio_metrics['total_real_value'] += asset_value * (1 + real_roi)
            portfolio_metrics['inflation_burn'] += asset_value * cum_inflation
```

ve sonuç sözlüğündeki (satır 280-292) `'nominal_roi': a.roi` ve `'value': a.value` satırlarını `'nominal_roi': nominal_roi * 100` ve `'value': asset_value` yap.

- [ ] **Step 5: `_run_single_scenario_sim` girişinde aynı deseni uygula**

`generate_monte_carlo_paths` metodunu değiştir (satır 76-95 civarı). Mevcut:

```python
        total_income = sum(t.amount for t in recent_tx if t.type == 'Gelir')
        total_expenses = sum(t.amount for t in recent_tx if t.type == 'Gider')
        monthly_savings = max(0.0, (total_income - total_expenses) / 12) if total_income > 0 else 0.0
        annual_savings = monthly_savings * 12

        inflation = self.settings.annual_inflation or 0.40
        years = self.settings.mc_years or 30
        sims = min(self.settings.mc_simulations or 10000, 10000)  # Aşırı yavaşlamayı önlemek için 10.000 ile sınırlı
```

Yeni:

```python
        total_income = float(sum(t.amount for t in recent_tx if t.type == 'Gelir'))
        total_expenses = float(sum(t.amount for t in recent_tx if t.type == 'Gider'))
        monthly_savings = max(0.0, (total_income - total_expenses) / 12) if total_income > 0 else 0.0
        annual_savings = monthly_savings * 12

        inflation = float(self.settings.annual_inflation or 0.40)
        years = self.settings.mc_years or 30
        sims = min(self.settings.mc_simulations or 10000, 10000)  # Aşırı yavaşlamayı önlemek için 10.000 ile sınırlı
```

ve birkaç satır altında (satır 104-106):

```python
        active_scenario = self.settings.mc_scenario or 'balanced'
        active_mu = self.settings.mc_expected_return or scenarios[active_scenario]['mu']
        active_sigma = self.settings.mc_volatility or scenarios[active_scenario]['sigma']
```

Yeni:

```python
        active_scenario = self.settings.mc_scenario or 'balanced'
        active_mu = float(self.settings.mc_expected_return or scenarios[active_scenario]['mu'])
        active_sigma = float(self.settings.mc_volatility or scenarios[active_scenario]['sigma'])
```

Son olarak `page_context`'te (`domain/analysis/services/strategy_service.py:23`) `total_investable = sum(a.value for a in assets) + get_actual_cash()` satırını da aynı sınır kuralına uy:

```python
        total_investable = float(sum(a.value for a in assets)) + float(get_actual_cash() or 0)
```

- [ ] **Step 6: Testi tekrar çalıştır, geçtiğini doğrula**

```powershell
.venv\Scripts\python.exe -m pytest tests/test_strategy_engine_regression.py -v
```

Beklenen: **PASS**.

- [ ] **Step 7: Tam regresyonu çalıştır**

```powershell
.venv\Scripts\python.exe -m pytest tests/ -q
```

Beklenen: mevcut tüm testler (Decimal precision testleri dahil) geçmeye devam etmeli — bu değişiklik yalnızca analitik motorun girişini etkiliyor, `Transaction.amount`/`Asset.value` DB tipini değil.

- [ ] **Step 8: Commit**

```bash
git add domain/analysis/services/strategy_engine.py domain/analysis/services/strategy_service.py tests/test_strategy_engine_regression.py
git commit -m "fix: convert Decimal fields to float at strategy analytics boundary

Root cause: SPRINT-01 migrated Asset.value/roi and StrategySettings.* to
Decimal, but strategy_engine.py mixed them with raw float literals inside
numpy Monte Carlo / real-yield calculations, causing a guaranteed 500 on
/strategy for any asset with a purchase cost basis."
```

---

### Task 0.3: Hotfix — `list_transactions()` tüm tenant'ların verisini sızdırıyor (H5)

**Files:**
- Modify: `repositories/financial_repository.py`
- Test: `tests/test_tenant_isolation.py`

**Interfaces:**
- Consumes: `self._resolve_tenant_id(tenant_id)` — zaten `repositories/financial_repository.py:13-23`'te var, aynı sınıfın diğer 5 metodu tarafından kullanılıyor.
- Produces: `list_transactions(tenant_id=None, order_desc=True)` — artık tenant_id verilmezse Flask `g.tenant_id`'den otomatik çözer, hiçbir context yoksa `RuntimeError` fırlatır (sessiz global fallback YOK). `domain/planning/services/plan_service.py`'deki çağrı siteleri **değişmeden** çalışmaya devam eder çünkü `_resolve_tenant_id` zaten `g.tenant_id`'yi otomatik okuyor.

- [ ] **Step 1: Sızıntıyı kanıtlayan başarısız testi yaz**

`tests/test_tenant_isolation.py` dosyasının sonuna ekle:

```python
def test_list_transactions_without_tenant_id_does_not_leak_other_tenants(app):
    """financial_repository.list_transactions() tenant_id verilmezse
    _resolve_tenant_id() ile g.tenant_id'ye dusmeli, TUM tenant'lari
    degil. Regression for: payment_calendar_context() ve daily_balance()
    (domain/planning/services/plan_service.py) tum tenant'larin
    toplamini gosteriyordu.
    """
    from database import add_transaction
    from repositories.financial_repository import FinancialRepository

    tenant1 = Tenant(id='tenant1', name='Tenant 1')
    tenant2 = Tenant(id='tenant2', name='Tenant 2')
    db.session.add_all([tenant1, tenant2])
    db.session.flush()

    add_transaction('2025-01-01', 'Maaş', 'T1', 'Gelir', 1000, 'Ödendi', tenant_id='tenant1')
    add_transaction('2025-01-01', 'Maaş', 'T2', 'Gelir', 2000, 'Ödendi', tenant_id='tenant2')

    repo = FinancialRepository()

    with app.test_request_context('/'):
        from flask import g
        g.tenant_id = 'tenant1'
        result = repo.list_transactions(order_desc=False)

    assert len(result) == 1
    assert result[0].amount == 1000


def test_list_transactions_without_tenant_context_raises(app):
    """Flask request context disinda ve tenant_id verilmeden cagrilirsa
    sessizce global veri donmemeli, hata firlatmali."""
    from repositories.financial_repository import FinancialRepository

    repo = FinancialRepository()
    with app.app_context():
        import pytest
        with pytest.raises(RuntimeError):
            repo.list_transactions()
```

- [ ] **Step 2: Testleri çalıştır, ilkinin şu anki (sızdıran) davranışla nasıl davrandığını gözlemle**

```powershell
.venv\Scripts\python.exe -m pytest tests/test_tenant_isolation.py::test_list_transactions_without_tenant_id_does_not_leak_other_tenants tests/test_tenant_isolation.py::test_list_transactions_without_tenant_context_raises -v
```

Beklenen: İlk test **PASS** olabilir (çünkü `g.tenant_id` set edilmişken mevcut kod da `if tenant_id:` check'i `g`'den okumadığı için aslında `tenant_id=None` kalır ve filtre uygulanmaz — yani sonuç 2 kayıt döner, `len(result) == 1` assertion'ı **FAIL** verir). İkinci test kesin **FAIL** verir çünkü mevcut kod `RuntimeError` değil, sessizce tüm kayıtları döner.

- [ ] **Step 3: `list_transactions`'ı diğer 5 metodun deseniyle hizala**

`repositories/financial_repository.py` satır 35-40. Mevcut:

```python
    def list_transactions(self, tenant_id=None, order_desc=True):
        query = Transaction.query
        if tenant_id:
            query = query.filter_by(tenant_id=tenant_id)
        order = Transaction.date.desc() if order_desc else Transaction.date.asc()
        return query.order_by(order).all()
```

Yeni:

```python
    def list_transactions(self, tenant_id=None, order_desc=True):
        tenant_id = self._resolve_tenant_id(tenant_id)
        query = Transaction.query.filter_by(tenant_id=tenant_id)
        order = Transaction.date.desc() if order_desc else Transaction.date.asc()
        return query.order_by(order).all()
```

- [ ] **Step 4: Testleri tekrar çalıştır**

```powershell
.venv\Scripts\python.exe -m pytest tests/test_tenant_isolation.py -v
```

Beklenen: tüm testler **PASS**, `test_list_transactions_without_tenant_context_raises` dahil.

- [ ] **Step 5: `list_transactions`'ın diğer çağrı sitelerini kırmadığını doğrula**

```powershell
.venv\Scripts\python.exe -m pytest tests/ -q
```

`infrastructure/export/export_service.py:56` ve `domain/reporting/services/dashboard_service.py:39` zaten `tenant_id=tenant_id` ile açıkça çağırıyor — etkilenmemeleri gerekir. `domain/planning/services/plan_service.py:71,97` hiç parametre değişikliği gerektirmiyor çünkü `_resolve_tenant_id(None)` otomatik `g.tenant_id`'yi okuyacak — request context'i olmayan bir çağrı (örn. arka plan job) varsa bu test çalıştırmasında ortaya çıkacak; çıkarsa o çağrı sitesine `tenant_id=` eklemek gerekir, bu adımda raporla.

- [ ] **Step 6: Commit**

```bash
git add repositories/financial_repository.py tests/test_tenant_isolation.py
git commit -m "fix: close cross-tenant leak in FinancialRepository.list_transactions

Root cause: this was the only method in the class not calling
_resolve_tenant_id(); domain/planning/services/plan_service.py's
payment_calendar_context() and daily_balance() called it with no
tenant_id, aggregating every tenant's transactions into figures shown
on the Payment Calendar page and Monthly Dashboard chart."
```

---

# PHASE 1 — Kalan Gerçek Tenant Açıkları

**Önemli:** `tenant_phase1_gap_inventory.md`'nin P0 listesinin çoğu (get_transaction/update_transaction/delete_transaction/transaction_page, user_repository'nin platform-vs-tenant ayrımı) **zaten kodda düzeltilmiş** durumda — doküman güncelliğini yitirmiş, körü körüne uygulanmamalı. Aşağıdaki task, kod okuyarak doğrulanmış **tek kalan gerçek P0** üzerine kurulu.

### Task 1.1: `portfolio_repository` — unscoped asset erişimi

**Files:**
- Modify: `repositories/portfolio_repository.py`
- Test: `tests/test_tenant_scoped_analytics.py` (mevcut dosyaya ekle) veya `tests/test_tenant_isolation.py`

**Doğrulanmış durum:** `update_asset()`, `bulk_update_assets()`, `get_asset_update_history()` tenant_id parametresi almıyor / `self.db.session.get(Asset, asset_id)` ile doğrudan ID üzerinden erişiyor (`repositories/portfolio_repository.py:53-140`). Bu, `tenant_phase1_gap_inventory.md`'nin P1 listesinde doğru tespit edilmiş, hâlâ geçerli.

- [ ] **Step 1: Sızıntıyı kanıtlayan test**

```python
def test_update_asset_cannot_modify_other_tenants_asset(app):
    """portfolio_repository.update_asset() tenant siniri olmadan calisir;
    baska tenant'in asset'i ID tahmin edilerek guncellenebilir."""
    from decimal import Decimal

    from domain.portfolio.models.portfolio_models import Asset
    from repositories.portfolio_repository import PortfolioRepository

    tenant1 = Tenant(id='tenant1', name='Tenant 1')
    tenant2 = Tenant(id='tenant2', name='Tenant 2')
    db.session.add_all([tenant1, tenant2])
    db.session.flush()

    sector = AssetSector.query.filter_by(name='Teknoloji').first()
    victim_asset = Asset(
        type='Hisse Senedi', name='Kurban Varlik', value=Decimal('1000'),
        purchase_date='2024-01-01', purchase_cost=Decimal('1000'),
        quantity=Decimal('10'), unit_price=Decimal('100'), currency='TRY',
        symbol='VCT', risk_level='Orta', liquidity='Likit',
        sector_id=sector.id, tenant_id=tenant1.id,
    )
    db.session.add(victim_asset)
    db.session.commit()
    victim_id = victim_asset.id

    repo = PortfolioRepository()
    with app.test_request_context('/'):
        from flask import g
        g.tenant_id = 'tenant2'
        # tenant2 olarak tenant1'in asset'ini guncellemeye calis
        with pytest.raises((PermissionError, LookupError)):
            repo.update_asset(
                asset_id=victim_id, type_='Hisse Senedi', name='Ele Gecirildi',
                value=Decimal('1'), description='', tenant_id='tenant2',
            )
```

- [ ] **Step 2: Çalıştır, `PermissionError`/`LookupError` fırlatmadığını (test FAIL) doğrula**

```powershell
.venv\Scripts\python.exe -m pytest tests/test_tenant_isolation.py::test_update_asset_cannot_modify_other_tenants_asset -v
```

- [ ] **Step 3: `update_asset`/`bulk_update_assets`/`get_asset_update_history`'ye `TenantScopedRepository` primitive'lerini uygula**

`repositories/portfolio_repository.py`'nin sınıf tanımının `TenantScopedRepository`'den türediğini doğrula (`repositories/base.py:40`'taki sınıf); değilse import ve miras zincirini güncelle. Sonra her üç metoda `tenant_id` parametresi ekle ve gövdede ilk satır olarak:

```python
tenant_id = self.require_tenant_id(tenant_id)
asset = self.get_for_tenant(Asset, asset_id, tenant_id)
self.assert_same_tenant(asset, tenant_id)
```

deseniyle `self.db.session.get(Asset, asset_id)` çağrılarının yerini al (bu üç metod, `repositories/base.py:82-99`'daki `get_for_tenant`/`assert_same_tenant` ile birebir örtüşüyor — yeni bir primitive icat etmeye gerek yok).

- [ ] **Step 4-6: Test geçene kadar tekrarla, tam regresyon çalıştır, commit**

(Task 0.2/0.3 ile aynı üç adım — kısaltıldı, engineer aynı komutları kullanır: `pytest tests/test_tenant_isolation.py -v`, `pytest tests/ -q`, `git commit`.)

---

## Self-Review (writing-plans skill gereği)

1. **Spec kapsaması:** H1-H5'in her biri Phase 0'da bir task'a karşılık geliyor (H1→0.1, H2→0.1, H3→0.1, H4→0.2, H5→0.3). Phase 1, doğrulanmış tek kalan P0'ı kapsıyor. Phase 2-6 kasıtlı olarak bu dokümanda detaylandırılmadı (scope check) — kullanıcı onayı sonrası ayrı plan olarak yazılacak.
2. **Placeholder taraması:** Her adımda gerçek dosya yolları, gerçek satır aralıkları, gerçek (okunmuş, uydurulmamış) mevcut kod ve gerçek yeni kod var. "TODO" / "benzer şekilde" yok.
3. **Tip/isim tutarlılığı:** `_resolve_tenant_id`, `require_tenant_id`, `get_for_tenant`, `assert_same_tenant` isimleri `repositories/base.py` ve `repositories/financial_repository.py`'den birebir okunarak kullanıldı, uydurulmadı.

---

## Sonraki Adım

Phase 0 + Phase 1 uygulanınca `/strategy` çöküyor olmaktan çıkar, ödeme takvimi/aylık grafik doğru tenant'ı gösterir, `ruff`/`import-linter` gerçekten çalışabilir hale gelir ve rate limiting her ortamda tutarlı biçimde aktif olur — yani **localhost'ta gerçek bir test turu yapılabilir hale gelir.**

Phase 2 (kalan Decimal/float sınırları), Phase 3 (`app/` kararı), Phase 4 (Postgres + health check + prod sertleştirme, docker-compose ile localhost'ta), Phase 5 (önceki turda konuşulan hook/subagent kurulumu) için de aynı derinlikte ayrı plan dokümanları hazırlayabilirim.
