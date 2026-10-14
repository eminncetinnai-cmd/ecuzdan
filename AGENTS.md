# AGENTS.md — Development Standards & Governance for AI Agents

Welcome, AI Agent! When implementing features, fixing bugs, or refactoring in this repository, you must follow the architecture and design rules below.

---

## 🗺️ 0. Codebase Map (Read This First — Saves Token Lookups)

### Directory Purpose Reference
| Directory | Purpose | What NOT to do here |
|-----------|---------|---------------------|
| `domain/` | Pure business logic (services, entities, value objects) | Import Flask, SQLAlchemy models |
| `application/` | Use cases, workflow orchestration, DTOs | Direct DB access, Flask imports |
| `infrastructure/` | DB sessions, external APIs, background workers | Business logic |
| `repositories/` | SQLAlchemy queries and persistence | Business rules |
| `routes/` | Flask blueprints, HTTP handling, template rendering | Business logic |
| `templates/` | Jinja2 HTML (extends `layout.html`) | Inline styles, hardcoded colors |
| `templates/macros/` | Reusable UI components | Direct HTML duplication |
| `static/css/` | CSS tokens and component styles | Inline styles in HTML |
| `engines/` | Financial calculation engine, live data aggregation | Flask imports |
| `shared/` | Cross-layer utilities (currency, formatting) | Layer-specific logic |
| `scripts/` | Governance, CI, migration scripts | Application logic |
| `tests/unit/` | Unit tests (fast, no DB) | Integration tests |
| `tests/integration/` | Integration tests (DB-backed) | Unit-only logic |

### Key Files Quick Reference
| File | What It Does |
|------|-------------|
| `app.py` | Flask app factory, blueprint registration, limiter setup |
| `routes/__init__.py` | Global filters (`format_money`, `format_ticker_price`), context processor (`live`, `base_currency_*`) |
| `engines/financial_engine.py` | `get_live_data()`, financial analysis, KPI calculations |
| `infrastructure/background/background_service.py` | Background thread: live FX/gold, weather, market data |
| `domain/analysis/services/fx_metals_provider.py` | Multi-provider FX+gold chain (doviz.com → TCMB → Frankfurter → GoldAPI → yfinance) |
| `shared/currency_precision.py` | `get_currency_symbol()`, `get_asset_type_scale()` |
| `utils/format_utils.py` | `format_money()`, `format_date()`, `today_display()` |
| `models.py` | SQLAlchemy models (Transaction, Asset, RecurringPlan, User, Tenant, etc.) |
| `templates/layout.html` | Master layout: top bar (live ticker), sidebar, header, breadcrumbs |
| `static/css/design-tokens.css` | CSS custom properties (color, spacing, shadow tokens) |
| `scripts/check_design_system.py` | Design system linter (run with `--ratchet`) |
| `docs/AI_AGENT_DESIGN_SYSTEM.md` | Full macro cheatsheet — READ before writing any template |

### Context Processor Variables (Available in All Templates)
```
live.usd, live.eur, live.gold, live.weather   → Top-bar ticker values
base_currency_code, base_currency_symbol       → User's base currency (e.g. TRY / ₺)
current_user, user_theme, privacy_mode         → Auth & display state
date_str, today_display, current_day           → Date/time display
```

---

## 🚑 Quick Fix Lookup (Known Bugs & Their Solutions)

| Symptom | Root Cause | Fix |
|---------|-----------|-----|
| Chart bars show as solid **black** | `ctx.fillStyle` can't parse `var(--css-var)` | Use `resolveColor('--var-name', '#fallback-hex')` in JS |
| Button shows `<SVG CLASS="...">` as raw text | Jinja auto-escapes HTML in macro params | Use `{{ icon\|safe }}` in macro definition |
| Gold price shows 20+ decimal digits | `Decimal.normalize()` on full precision value | `_format_decimal(value, 'gold')` rounds to 2 dp |
| Template changes not visible in browser | Flask template cache in memory | Set `TEMPLATES_AUTO_RELOAD=True` in `app.py`; restart server |
| `canvas` chart colors wrong after CSS refactor | Chart.js doesn't read computed CSS variables | Always resolve hex at chart init: `getComputedStyle(doc).getPropertyValue(...)` |
| Monitoring page dark when app is light | `body:has(.monitoring-container)` overriding global bg | Remove dark body overrides; use `background: transparent` in page CSS |

### Chart Color Standards (Use These Hex Values in Canvas JS)
```js
const CHART_COLORS = {
  income:     '#10b981',  // Emerald-500  — Gelir
  expense:    '#ef4444',  // Rose-500     — Gider
  investment: '#0ea5e9',  // Sky-500      — Yatırım
  purple:     '#6366f1',  // Indigo-500   — Genel
  amber:      '#f59e0b',  // Amber-500    — Uyarı / Altın
};
```

---

## 🏛️ 1. Architecture Layering & Security (EAFGS)

- **Domain Layer (`domain/`):** Pure business logic. Must NEVER import Flask (`from flask import ...`) or database models directly.
- **Application Layer (`application/`):** Use cases, services, and workflow orchestration.
- **Infrastructure Layer (`infrastructure/`, `repositories/`, `database/`):** Database sessions, SQL migrations, external API clients.
- **Presentation Layer (`routes/`, `templates/`):** Flask blueprints, Jinja2 templates, and responses.
- **Multi-Tenant Isolation:** Always filter database queries with `tenant_id` and `user_id`. Never bypass tenant checks.
- **Fail-Closed Security:** Sensitive operations (backups, password resets, financial changes) must be guarded with CSRF protection, rate limits, and audit logging.

---

## 🎨 2. Design System & UI Rules

- **Consult the full cheatsheet:** Read [`docs/AI_AGENT_DESIGN_SYSTEM.md`](docs/AI_AGENT_DESIGN_SYSTEM.md) before writing any UI template.
- **No inline styles:** Do not use `style="..."` in templates.
- **No hardcoded colors:** Do not use hex/rgb codes in HTML. Use Tailwind tokens (`text-slate-800`, `bg-indigo-600`) or CSS variables (`var(--color-primary)`).
- **Dynamic currency everywhere:** Use `{{ base_currency_symbol }}` and `{{ a.currency|currency_symbol or base_currency_symbol }}` in templates. In JS, use `window.BASE_CURRENCY_SYMBOL` / `window.BASE_CURRENCY_CODE`.
- **Use standard Jinja2 macros:** Import from `templates/macros/` (`buttons.html`, `forms.html`, `cards.html`, `ui.html`, `charts.html`, `tables.html`). For modal dialogs, use global widgets from `templates/widgets/` (`confirm_modal.html`, `quick_tx_modal.html`, etc.).

### Jinja Template Filters (Registered in `routes/__init__.py`)
| Filter | Usage | Output |
|--------|-------|--------|
| `\|format_money` | `{{ amount\|format_money }}` | `<span class="amount">1.234,56</span>` |
| `\|format_date` | `{{ date_str\|format_date }}` | `1 Eylül 2026` |
| `\|format_ticker_price` | `{{ live.gold\|format_ticker_price }}` | `6.894,70` (2 dp, Türkçe) |
| `\|currency_symbol` | `{{ 'USD'\|currency_symbol }}` | `$` |
| `\|asset_color` | `{{ loop.index\|asset_color }}` | `#fbbf24` |

---

## 🛡️ 3. Quality & Governance Gates

Always verify your changes before finishing:
```powershell
# 1. Check design system consistency (MUST be 0 issues)
python scripts/check_design_system.py --ratchet

# 2. Run unit tests (MUST all pass)
python -m pytest tests/unit/ -q --no-cov

# 3. Verify Architecture Gate (MUST pass with 0 violations in BLOCK mode)
powershell -ExecutionPolicy Bypass -File scripts/governance/run_architecture_gate.ps1 -Mode BLOCK

# 4. Verify Static Type Check (Mypy — MUST be 0 errors)
python scripts/check_type_annotations.py

# 5. Master Pre-Flight Smoke Gate (MUST be 0 template errors & 0 route 500s)
python scripts/preflight_check.py
```

---

## ⚡ 4. New Feature Checklist

When adding a new feature, work in this order:
1. **Domain/Application layer** → business logic, no Flask
2. **Repository** → DB query with `tenant_id` filter
3. **Route (Blueprint)** → HTTP handler in `routes/<feature>.py`
4. **Template** → extends `layout.html`, uses macros
5. **Register blueprint** in `app.py`
6. **Run gates** → design check + tests + architecture gate

> For full guidance, see [`docs/AGENT_QUICKREF.md`](docs/AGENT_QUICKREF.md)
