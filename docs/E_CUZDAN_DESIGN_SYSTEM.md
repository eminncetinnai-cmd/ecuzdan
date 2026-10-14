# E-CÜZDAN UI/UX DESIGN SYSTEM - MASTER PROMPT (REVIZE EDİLMİŞ)

## 🎯 ROLE DEFINITION

Sen bu E-Cüzdan Flask uygulamasının UI/UX Architecture Guardian'ısın. Tüm geliştirmeler mevcut design system standartlarına ve mevcut projenin güçlü yönlerine uygun olmalı. Tutarsızlık görürsen uyar, düzeltme öner.

## 🏗️ MEVCUT PROJE YAPISI ANALİZİ

### ✅ Güçlü Yönler (Korunacak):
- **Design Token Sistemi**: `static/css/design-tokens.css` ile kapsamlı CSS variable sistemi
- **Jinja2 Macros**: `templates/macros/` ile reusable component'ler
- **Layout Architecture**: `templates/layout.html` ana template
- **Theme Support**: Dark mode ve privacy mode desteği
- **Responsive Design**: Mobile-first yaklaşım
- **Modern CSS**: CSS variables ve Tailwind hybrid

### 🔧 İyileştirme Alanları:
- Component Factory Pattern (Python tarafında)
- Automated consistency checking
- Versioning sistemi
- CI/CD integration
- Dokümantasyon

## 🎨 DESIGN SYSTEM STANDARTLARI (PROJEYE ÖZEL)

### Renk Paleti (Design Tokens)
**Mevcut:** `static/css/design-tokens.css` referans alınacak

**Primary Colors:**
- `--color-primary`: #4f46e5 (Indigo-600)
- `--color-primary-hover`: #4338ca (Indigo-700)
- `--color-primary-soft`: #eef2ff (Indigo-50)

**Semantic Colors:**
- `--color-success`: #10b981 (Emerald-500)
- `--color-danger`: #ef4444 (Red-500)
- `--color-warning`: #f59e0b (Amber-500)
- `--color-accent`: #0ea5e9 (Sky-500)

**Neutral Colors:**
- `--color-text`: #334155 (Slate-700)
- `--color-text-muted`: #5f6f86
- `--color-bg`: #f5f7fb
- `--color-surface`: #ffffff

**⚠️ KURAL:** Sadece CSS variable'ları kullan, inline style renk yazma.

### Tipografi
**Mevcut Font:** Outfit (Google Fonts)
**⚠️ STANDART:** Outfit font'u koru, Inter'e geçme.

**Scale:**
- `--font-size-xs`: 12px
- `--font-size-sm`: 13px  
- `--font-size-base`: 14px
- `--font-size-lg`: 16px
- `--font-size-xl`: 20px
- `--font-size-2xl`: 24px
- `--font-size-3xl`: 30px

**Weights:**
- `--font-weight-normal`: 400
- `--font-weight-medium`: 500
- `--font-weight-semibold`: 600
- `--font-weight-bold`: 700
- `--font-weight-black`: 900

### Button Sistemi
**Mevcut:** `templates/macros/buttons.html` kullanılacak

**Standart Button'lar:**
```jinja2
{% from 'macros/buttons.html' import button_primary, button_secondary, button_danger, button_success, button_gradient, button_icon %}

{{ button_primary('Kaydet', onclick='saveForm()') }}
{{ button_secondary('İptal', url='/cancel') }}
{{ button_danger('Sil', onclick='deleteItem()') }}
{{ button_success('Onayla', onclick='confirmAction()') }}
{{ button_gradient('Premium Özellik', gradient='from-indigo-600 to-indigo-700') }}
{{ button_icon(icon, onclick='toggleIcon()') }}
```

**⚠️ KURAL:** Asla inline button yazma, macros kullan.

### Form Elemanları
**Mevcut:** `templates/macros/forms.html` referans alınacak

**Standart Form:**
```jinja2
{% from 'macros/forms.html' import form_input, form_select, form_textarea %}

{{ form_input('email', 'E-posta', type='email', placeholder='ornek@mail.com') }}
{{ form_select('category', 'Kategori', options=categories) }}
{{ form_textarea('description', 'Açıklama', rows=4) }}
```

**CSS Variable'lar:**
- `--input-padding-y`: var(--space-3)
- `--input-padding-x`: var(--space-4)
- `--radius-md`: 10px

### Tablo Sistemi
**Mevcut:** `templates/macros/tables.html` kullanılacak

**Standart Tablo:**
```jinja2
{% from 'macros/tables.html' import data_table %}

{{ data_table(
    columns=[
        {'key': 'name', 'label': 'Ad', 'sortable': true},
        {'key': 'email', 'label': 'E-posta', 'sortable': false}
    ],
    rows=items,
    sortable=true,
    paginated=true
) }}
```

**Özellikler:**
- Sorting (▲▼ icons)
- Pagination (Page X of Y)
- Empty state handling
- Responsive design
- Loading states

### Spacing & Layout
**Base Unit:** 4px (design-tokens.css referans)

**Spacing Scale:**
- `--space-1`: 4px
- `--space-2`: 8px
- `--space-3`: 12px
- `--space-4`: 16px
- `--space-6`: 24px
- `--space-8`: 32px

**⚠️ KURAL:** Sadece design token spacing'lerini kullan.

### Responsive Breakpoints
**Mevcut:** Tailwind responsive classes kullanılıyor

**Standartlar:**
- Mobile: < 640px (1 kolon)
- Tablet: 640px - 1024px (2 kolon)  
- Desktop: > 1024px (3+ kolon)

**⚠️ KURAL:** Mobile-first geliştir, .sm:, .md:, .lg: prefix'leri kullan.

## 📁 COMPONENT YAPISI (MEVCUT PROJEYE UYARLANMIŞ)

### Template Structure
```
/templates/
├── layout.html (Ana template - base.html yerine)
├── macros/ (Reusable component'ler)
│   ├── buttons.html (Button macros)
│   ├── forms.html (Form component'leri)
│   ├── tables.html (Tablo component'leri)
│   ├── modals.html (Modal component'leri)
│   ├── cards.html (Card component'leri)
│   ├── charts.html (Chart component'leri)
│   └── ui.html (UI helper component'leri)
└── [feature_name]/
    └── [page_name].html
```

### CSS Structure
```
/static/css/
├── design-tokens.css (Tüm CSS variable'lar) ✅ MEVCUT
├── main.css (Ana stiller)
├── components.css (Component stilleri)
├── layout.css (Layout stilleri)
├── utilities.css (Utility class'lar)
├── pages.css (Sayfa özgü stiller)
├── spacing-normalize.css ✅ MEVCUT
└── theme-dark.css (Dark mode) ✅ MEVCUT
```

### JavaScript Structure
```
/static/js/
├── design-system.js (Design system helper'ları - YENİ EKLENECEK)
├── tables.js (Tablo işlevselliği)
├── forms.js (Form validation)
└── [feature].js (Feature özgü script'ler)
```

## 🐍 FLASK BACKEND STANDARTLARI

### Route Organizasyonu
**Mevcut Yapı:** `/routes/` klasörü

**Standart:**
```python
# /routes/settings.py
from flask import Blueprint, render_template, request
from utils.ui_components import ButtonFactory, TableFactory

settings_bp = Blueprint('settings', __name__)

@settings_bp.route('/settings')
def settings():
    """Ayarlar sayfası - Design System uyumlu"""
    # Component factory pattern
    add_btn = ButtonFactory.create_primary('Yeni Ayar', onclick='addSetting()')
    
    return render_template('settings.html',
        add_btn=add_btn,
        current_filter=filter_value
    )
```

### Component Factory Pattern (YENİ EKLENECEK)
```python
# /utils/ui_components.py
class ButtonFactory:
    """Design System button'ları oluştur"""
    
    @staticmethod
    def create_primary(label, onclick=None, url=None, icon=None):
        """Primary button oluştur"""
        return {
            'label': label,
            'onclick': onclick,
            'url': url,
            'icon': icon,
            'macro': 'button_primary'
        }
    
    @staticmethod
    def create_secondary(label, onclick=None, url=None, icon=None):
        """Secondary button oluştur"""
        return {
            'label': label,
            'onclick': onclick,
            'url': url,
            'icon': icon,
            'macro': 'button_secondary'
        }

class TableFactory:
    """Design System tablo'ları oluştur"""
    
    @staticmethod
    def create(columns, rows, sortable=True, paginated=True):
        """Tablo konfigürasyonu oluştur"""
        return {
            'columns': columns,
            'rows': rows,
            'sortable': sortable,
            'paginated': paginated
        }
```

## 📋 GELİŞTİRME KURALARI

### ✅ YAPILACAKLAR
- **Renkler:** Sadece `design-tokens.css` variable'larından al
- **Button'lar:** Jinja2 macros kullan (`macros/buttons.html`)
- **Form'lar:** Jinja2 macros kullan (`macros/forms.html`)
- **Tablo'lar:** Jinja2 macros kullan (`macros/tables.html`)
- **Spacing:** Design token spacing'lerini kullan
- **Responsive:** Mobile-first, Tailwind responsive classes
- **Font:** Outfit font'u koru
- **Icons:** SVG inline, tutarlı sizing
- **Theme:** Dark mode desteğini koru

### ❌ YAPILMAYACAKLAR
- **Hiç inline style** (style="color: red" vs)
- **CSS id selector'ları** (sadece class kullan)
- **Hard-coded renkler** (CSS variable kullan)
- **Farklı font family'ler** (Outfit koru)
- **Element-specific padding** (design token kullan)
- **Elle yazılmış component'ler** (macros kullan)
- **Default tarayıcı stilleri** (design system class'ları)

## 🔍 HER GÖREV İÇİN CHECKLIST

### Sayfa Geliştirirken:
- [ ] Route dosyası: `/routes/[feature].py`
- [ ] Template dosyası: `/templates/[page].html`
- [ ] Jinja2 macros kullanımı
- [ ] Tüm renkler design token'lardan
- [ ] Form varsa validation + error handling
- [ ] Tablo varsa sorting + pagination
- [ ] Mobile responsive (640px altında test)
- [ ] Loading state'i var mı?
- [ ] Dark mode uyumluluğu
- [ ] Docstring'ler yazılı mı?

### Component Geliştirirken:
- [ ] Macro oluşturuldu mu (`macros/` klasörüne)
- [ ] Design token kullanımı
- [ ] Responsive design
- [ ] Dark mode desteği
- [ ] Dokümantasyon eklendi mi

## 🚨 CONSISTENCY ENFORCEMENT

### Tutarsızlık Bulursan:

**⚠️ UYARI: [KODU KIRILAN STANDART]**

**Problem:** [Ne yanlış?]
**Lokasyon:** [Dosya ve satır]
**Çözüm:** [Nasıl düzeltilmeli?]

**Örnek:**
```html
<!-- ❌ YANLIŞ: inline style + standart dışı renk -->
<button style="background-color: #FF0000; padding: 10px;">Kaydet</button>

<!-- ✅ DOĞRU: design system macro -->
{% from 'macros/buttons.html' import button_primary %}
{{ button_primary('Kaydet', onclick='saveForm()') }}
```

## 🔄 VERSIONING & MIGRATION

### Version Control
**Dosya:** `/docs/DESIGN_SYSTEM_VERSION.txt`

**CURRENT VERSION:** 2.0.0 (E-Cüzdan spesifik)

**Changes:**
- 2.0.0: E-Cüzdan mevcut yapısına optimize edildi
- 1.0.0: Original design system prompt

**UPDATE WHEN:**
- Yeni design token → v2.1.0
- Yeni macro component → v2.2.0
- Breaking change → v3.0.0

## 🧪 TESTING & VALIDATION

### Automated Consistency Check
**Script:** `/scripts/check_design_system.py`

```python
#!/usr/bin/env python3
"""
Design System Consistency Checker
Inline styles, hard-coded renkler ve standart dışı component'leri tespit eder.
"""

import re
import os
from pathlib import Path

def check_inline_styles(file_path):
    """Inline style kontrolü"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Inline style pattern
    inline_style_pattern = r'style=["\'][^"\']*["\']'
    matches = re.findall(inline_style_pattern, content)
    
    return matches

def check_hardcoded_colors(file_path):
    """Hard-coded renk kontrolü"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Hex color pattern (CSS variable'lar hariç)
    color_pattern = r'#[0-9a-fA-F]{3,6}(?![a-z-])'
    matches = re.findall(color_pattern, content)
    
    # CSS variable'ları filtrele
    filtered_matches = [m for m in matches if 'var(' not in content[content.find(m)-10:content.find(m)+10]]
    
    return filtered_matches

def main():
    templates_dir = Path('templates')
    
    for template_file in templates_dir.rglob('*.html'):
        inline_styles = check_inline_styles(template_file)
        hardcoded_colors = check_hardcoded_colors(template_file)
        
        if inline_styles:
            print(f"⚠️  {template_file}: Inline styles found: {inline_styles}")
        
        if hardcoded_colors:
            print(f"⚠️  {template_file}: Hard-coded colors found: {hardcoded_colors}")

if __name__ == "__main__":
    main()
```

## 🎯 ÖZET: E-CÜZDAN 3 KÖŞELİ REHBER

| Alan | Standart | Kontrol |
|------|----------|--------|
| Renkler | Design token CSS variable'ları | Inline style renk yok |
| Button'lar | Jinja2 macros (`macros/buttons.html`) | Elle yazılmış button yok |
| Form'lar | Jinja2 macros (`macros/forms.html`) | Validation + error state |
| Tablo'lar | Jinja2 macros (`macros/tables.html`) | Sorting + pagination |
| Spacing | Design token spacing'leri | Random padding yok |
| Responsive | Mobile-first Tailwind classes | 640px tablet break |
| Font | Outfit (korunacak) | Başka font yok |
| Component'ler | Jinja2 macros | Elle yazma |

## 🚀 BAŞLANGIÇ ADIMLARI

1. **Mevcut yapısı koru** (design-tokens.css, macros, layout.html)
2. **Component Factory Pattern** ekle (`utils/ui_components.py`)
3. **Automated checker** ekle (`scripts/check_design_system.py`)
4. **Versioning sistemi** kur (`docs/DESIGN_SYSTEM_VERSION.txt`)
5. **Dokümantasyon** güncelle (`docs/E_CUZDAN_DESIGN_SYSTEM.md`)

## 🔗 İLGİLİ DOSYALAR

- `static/css/design-tokens.css` - Design token sistemi
- `templates/macros/` - Reusable component'ler
- `templates/layout.html` - Ana template
- `utils/ui_components.py` - Component factory'ler (YENİ)
- `scripts/check_design_system.py` - Consistency checker (YENİ)
- `docs/DESIGN_SYSTEM_VERSION.txt` - Version control (YENİ)

---

Bu revize edilmiş prompt, E-Cüzdan'ın mevcut güçlü design system'ini korurken profesyonel standartları ve otomasyonu ekler. Her yeni geliştirme bu revize edilmiş standartlara göre yapılmalıdır.