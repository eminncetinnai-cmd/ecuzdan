# ADR 002 — Jinja2 Makrolarında HTML/SVG Parametreler `|safe` Filtresi Zorunlu

**Tarih:** 2026-08-31
**Durum:** Aktif ✅
**Kategori:** Templates / Jinja2

---

## Sorun

`templates/macros/buttons.html` içindeki `button_primary`, `button_secondary` vb. makrolara `icon='<svg ...>'` gibi HTML içeriği parametre olarak geçildiğinde, tarayıcıda buton etiketi içinde `<SVG CLASS="W-3 H-3"...` şeklinde ham metin görünüyordu.

## Kök Neden

Jinja2'nin otomatik HTML escaping mekanizması (`autoescape=True`), şablon değişkenlerindeki `<`, `>`, `&` karakterlerini HTML entity'lerine çevirir:
- `<svg` → `&lt;svg`
- `>` → `&gt;`

Bu sayede XSS önlenir ama SVG ikonları da metin olarak çıkar.

## Karar

Makro tanımlarında HTML/SVG içeriği alan tüm parametreler `|safe` filtresi ile render edilecek:

```jinja2
{# YANLIŞ ❌ — Jinja escape eder #}
{% if icon %}{{ icon }}{% endif %}

{# DOĞRU ✅ — safe ile HTML olarak render et #}
{% if icon %}{{ icon|safe }}{% endif %}
```

## Etkilenen Dosyalar

- `templates/macros/buttons.html` — tüm buton makrolarındaki `icon` parametresi

## Güvenlik Notu

`|safe` filtresi yalnızca **güvenilir kaynaklardan** (backend Python kodu, sabit string değerler) gelen HTML için kullanılmalıdır. Kullanıcı girdisine asla `|safe` uygulanmaz.
