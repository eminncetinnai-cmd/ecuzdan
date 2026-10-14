# E-Cüzdan AI Agent Design System Guidelines & Cheatsheet

> **IMPORTANT FOR ALL AI AGENTS:**
> When generating or modifying any UI template or component in E-Cüzdan, you **MUST** adhere strictly to the rules below. Violations will be blocked by the Architecture Gate in CI and local test suites.

---

## 1. Core Mandates

### 🚫 STRICTLY FORBIDDEN
1. **NO inline styles:** Never use `style="padding: 10px; color: #10b981; ..."` in HTML.
2. **NO hardcoded hex/RGB colors in HTML:** Use Tailwind color tokens (`text-emerald-600`, `bg-slate-900`, `border-indigo-500`) or CSS variables (`var(--color-primary)`).
3. **NO hardcoded currency symbols:** Never write `₺`, `$` or `TL` directly in HTML or JS. Always use `{{ base_currency_symbol }}` or `{{ a.currency|currency_symbol or base_currency_symbol }}` in Jinja, and `window.BASE_CURRENCY_SYMBOL || '₺'` in JavaScript.
4. **NO raw `<button>` tags when a macro applies:** Always import and use macros from `macros/buttons.html`.

---

## 2. Standard Jinja2 Macros & Boilerplates

### A. Buttons (`macros/buttons.html`)
```jinja2
{% from "macros/buttons.html" import button_primary, button_secondary, button_danger, button_success, button_gradient %}

{# Primary Action Button #}
{{ button_primary(text="Kaydet", submit=True, icon="💾") }}

{# Navigation Link Styled as Button #}
{{ button_primary(text="Yeni Varlık Ekle", url="/assets_management", icon="➕") }}

{# Secondary / Cancel #}
{{ button_secondary(text="Vazgeç", onclick="closeModal()") }}

{# Gradient Highlight Button #}
{{ button_gradient(text="Hızlı İşlem", url="/transactions", gradient="from-indigo-600 to-indigo-800") }}
```

### B. Form Inputs (`macros/forms.html`)
```jinja2
{% from "macros/forms.html" import form_input, form_select, form_textarea %}

{# Text Input #}
{{ form_input(name="title", label="İşlem Başlığı", placeholder="Market alışverişi", required=True) }}

{# Currency / Number Input with dynamic symbol label #}
{{ form_input(name="amount", label="Tutar (" ~ base_currency_symbol ~ ")", type="number", step="0.01", required=True) }}

{# Dropdown Select #}
{{ form_select(name="category", label="Kategori", options=[{'value': 'food', 'label': 'Gıda'}, {'value': 'tech', 'label': 'Teknoloji'}], required=True) }}
```

### C. KPI & Cards (`macros/cards.html`)
```jinja2
{% from "macros/cards.html" import kpi_card, alert_box %}

{# Summary Metric Card #}
{{ kpi_card(title="Toplam Varlık", value=total_wealth|format_money ~ " " ~ base_currency_symbol, subtitle="3 Portföy", color="emerald", trend="12.5%", trend_is_positive=True) }}

{# Alert Banner #}
{{ alert_box(title="Bilgi", message="Veriler TCMB üzerinden canlı güncellenmektedir.", type="info") }}
```

### D. UI Badges & Elements (`macros/ui.html`)
```jinja2
{% from "macros/ui.html" import badge, progress_bar %}

{# Status Badge #}
{{ badge(text="Aktif", type="success") }}
{{ badge(text="Beklemede", type="warning") }}

{# Progress Bar #}
{{ progress_bar(value=75, max=100, color="indigo-600", show_label=True) }}
```

---

## 3. Page Layout Template

When creating a new page, extend `layout.html` and use the standard layout wrapper:

```jinja2
{% extends "layout.html" %}

{% block content %}
<!-- Header Section -->
<div class="mb-10 flex flex-wrap justify-between items-end gap-4">
    <div>
        <h2 class="text-3xl font-black text-slate-900 tracking-tighter uppercase leading-none bg-gradient-to-r from-slate-900 to-indigo-900 bg-clip-text text-transparent">
            {{ _('page_title') }}
        </h2>
        <p class="text-xs font-bold text-slate-400 uppercase tracking-widest mt-2">
            {{ _('page_subtitle') }}
        </p>
    </div>
    <div class="flex items-center gap-3">
        {{ button_primary(text="Yeni Ekle", onclick="openCreateModal()", icon="➕") }}
    </div>
</div>

<!-- Main Container Card -->
<div class="premium-card p-6 md:p-8 bg-white/80 mb-8">
    <!-- Content goes here -->
</div>
{% endblock %}
```

---

## 4. Verification Check

Before concluding your task, always verify with:
```powershell
python scripts/check_design_system.py
powershell -ExecutionPolicy Bypass -File scripts/governance/run_architecture_gate.ps1 -Mode BLOCK
```
