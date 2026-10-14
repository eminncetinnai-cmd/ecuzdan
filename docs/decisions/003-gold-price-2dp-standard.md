# ADR 003 — Altın Fiyatı 2 Ondalık Basamakla Sınırlandırma

**Tarih:** 2026-08-31
**Durum:** Aktif ✅
**Kategori:** Domain / Formatting

---

## Sorun

Üst barda gösterilen ALTIN fiyatı `6894.700062286438665917888639 ₺` gibi 24+ ondalık basamakla görünüyordu.

## Kök Neden

Troy Ons → gram TRY hesaplaması tam Decimal aritmetiği ile yapılır:

```python
gold_try_gram = price_usd_oz * usd_try / GOLD_GRAMS_PER_TROY_OUNCE
# GOLD_GRAMS_PER_TROY_OUNCE = Decimal("31.1034768")
# Decimal bölümü tam hassasiyetle sonuç üretir → 20+ basamak
```

Ardından `_format_decimal(value)` → `format(value.normalize(), "f")` işlemi de tam hassasiyeti korur.

## Karar

1. **Domain katmanında:** `_format_decimal(value, key)` fonksiyonu `key == "gold"` ise `round(value, 2)` uygular.
2. **Şablon katmanında:** `{{ live.gold|format_ticker_price }}` filtresi 2 ondalık basamağa yuvarlar ve Türkçe binlik ayracı uygular.

## Uygulama

```python
# domain/analysis/services/fx_metals_provider.py
def _format_decimal(value: Decimal | None, key: str | None = None) -> str:
    if value is None or not value.is_finite() or value <= 0:
        return "--"
    if key == "gold":
        return format(round(value, 2).normalize(), "f")
    return format(value.normalize(), "f")
```

```jinja2
{# templates/layout.html #}
{{ live.gold|format_ticker_price }}  {# → "6.894,70" #}
```

## Etkilenen Dosyalar

- `domain/analysis/services/fx_metals_provider.py` — `_format_decimal()`
- `routes/__init__.py` — `@app.template_filter('format_ticker_price')`
- `templates/layout.html` — ticker bar
