# `utils/` — Sunum ve Oturum Katmanı Yardımcıları

Bu dizin, Flask HTTP katmanı, kullanıcı oturumları ve sunum yardımcılarını içerir.

---

## 🧭 Katman Sorumlulukları ve Sınırları

| Modül Grubu | Dosyalar | Görev Alanı |
|-------------|----------|-------------|
| **Web & Oturum** | `auth_helpers.py`, `ajax_helpers.py`, `request_context.py`, `decorators.py` | Flask request döngüsü, kullanıcı yetkilendirme ve AJAX yanıt standartları |
| **Arayüz & Sunum** | `ui_components.py`, `profile_image.py` | Profil görselleri, UI bileşen rendering yardımcıları |
| **Gözlemlenebilirlik** | `logging_config.py`, `log_actions.py`, `log_filters.py`, `log_redaction.py`, `log_viewer.py`, `monitoring_stream.py`, `structured_logging.py`, `otel_setup.py` | Sistem loglama, PII maskeleme ve SSE stream kanalları |
| **Geriye Dönük Uyumluluk Facade'ları** | `format_utils.py` | Asıl implementasyon `shared.format_utils`'e taşınmıştır; tüm çağrıcılar için facade görevi görür |

---

## 🚫 Burada Neler Yapılmamalıdır?
- **Saf İş Mantığı (Domain):** Finansal hesaplama veya defter kuralları `utils/` içine yazılmamalı, `domain/` katmanına konmalıdır.
- **Framework Bağımsız Fonksiyonlar:** Flask veya Werkzeug bağımlılığı olmayan saf matematiksel ve biçimlendirici araçlar `shared/` dizinine yerleştirilmelidir.
