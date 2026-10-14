# ADR 001 — Canvas Grafiklerde CSS Değişkeni Yasağı

**Tarih:** 2026-08-31
**Durum:** Aktif ✅
**Kategori:** UI / Frontend

---

## Sorun

Chart.js canvas elementleri için `backgroundColor` değerlerinde CSS token kullanıldığında (`var(--color-emerald-500)`) tüm sütunlar siyah (`#000000`) çıkıyordu.

## Kök Neden

HTML5 Canvas 2D context (`ctx.fillStyle`) CSS `var(...)` sözdizimini **parse edemez**. Tanımsız veya çözülemeyen değerler için `#000000` (siyah) döner. Bu, Chart.js'in `backgroundColor` property'sinde de geçerlidir.

## Karar

Canvas JS kodunda CSS değişkenleri **asla doğrudan kullanılmayacak**. Bunun yerine `resolveColor()` yardımcı fonksiyonu ile runtime'da computed hex değeri okunacak ve bir fallback hex sağlanacak.

## Uygulama

```javascript
// YANLIŞ ❌ — Canvas parse edemez, siyah çıkar
backgroundColor: 'var(--color-emerald-500)'

// DOĞRU ✅ — Runtime'da çöz, hex fallback ver
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

## Etkilenen Dosyalar

- `templates/monthly_dashboard.html`
- `templates/index.html`
- Gelecekte oluşturulacak tüm canvas içeren şablonlar

## Tasarım Sistemi Uyumluluğu

`check_design_system.py`, bir satırda hem hex hem de `var(` veya `--` geçiyorsa ihlal saymaz (fallback pattern). Bu karar tasarım sistemi linter'ı ile uyumludur.
