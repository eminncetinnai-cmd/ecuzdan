# `shared/` — Çapraz Katman Bağımsız Araçlar (Cross-Cutting Utilities)

Bu dizin, herhangi bir web framework'üne (Flask, Werkzeug) bağımlı olmayan, saf Python ile yazılmış çapraz katman finans, para birimi ve biçimlendirme araçlarını barındırır.

---

## 🧭 Temel Modüller

| Modül | Görev ve İçerik |
|-------|-----------------|
| `format_utils.py` | Para (`format_money`), tarih (`format_date`, `parse_date_input`), bugünün tarihi yardımcıları |
| `money.py` | `Money` değer nesnesi, hassas para aritmetiği |
| `decimal_precision.py` | Yüksek hassasiyetli `Decimal` yuvarlama ve ölçekleme |
| `currency_precision.py` | Para birimi sembolleri, varlık türü bazlı hassasiyet haritaları |
| `circuit_breaker.py` | Dış servis çağrıları için dayanıklılık ve kesici deseni |
| `query_profiler.py` | Veritabanı sorgu optimizasyonu ve N+1 sorgu denetimi |
| `db.py` | Paylaşılan SQLAlchemy veritabanı örneği (`db`) |

---

## 🚫 Burada Neler Yapılmamalıdır?
- Flask request nesnesine (`request`, `session`, `g`) doğrudan erişilmemelidir.
- Katmana özel HTML template veya HTTP yanıt mantığı eklenmemelidir.
