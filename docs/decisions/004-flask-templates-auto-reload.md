# ADR 004 — Flask Şablon Önbelleği: TEMPLATES_AUTO_RELOAD Zorunlu

**Tarih:** 2026-08-31
**Durum:** Aktif ✅
**Kategori:** Infrastructure / Flask

---

## Sorun

Şablon dosyaları (`templates/*.html`) düzenlendikten sonra değişiklikler tarayıcıda görünmüyordu. Sunucu yeniden başlatılmadan eski içerik gösterilmeye devam ediyordu.

## Kök Neden

Flask production modunda (`debug=False`) Jinja2 şablonlarını ilk yüklemede belleğe alır ve sonraki isteklerde disk yerine bellekten okur. Şablon dosyası değişse de Flask fark etmez.

## Karar

`app.py`'de geliştirme ortamında şablon önbelleği devre dışı bırakılır:

```python
# app.py — create_app() içinde
app.config['TEMPLATES_AUTO_RELOAD'] = True
app.jinja_env.auto_reload = True
```

## Etkilenen Dosyalar

- `app.py` — `create_app()` fonksiyonu

## Not

Production ortamında bu ayar performans kaybına yol açar. Üretim ortamında şablonların önbelleğe alınması istenir; bu yüzden bu ayar `DEBUG` flag'ine veya ortam değişkenine bağlanabilir. Şu an geliştirme ortamında sabit `True` olarak kalır.
