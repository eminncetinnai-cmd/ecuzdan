# Log & Observability Runbook — E-Cüzdan v15

## Hızlı Doğrulama

```powershell
python scripts/verify_observability.py
python scripts/check_log_pii.py
python -m pytest tests/unit/test_log_redaction.py tests/unit/test_log_filters.py tests/unit/test_request_context.py tests/unit/test_log_alert_monitor.py tests/integration/test_monitoring.py -q --no-cov
```

---

## Mimari Özet

| Katman | Bileşen | Dosya |
|--------|---------|-------|
| Log üretimi | Python logging + filters | `utils/logging_config.py` |
| PII koruması | Maskeleme + redaksiyon | `utils/log_redaction.py`, `utils/log_filters.py` |
| Korelasyon | X-Request-ID + OTel trace | `utils/request_context.py` |
| Structured | JSON loglar | `utils/structured_logging.py` |
| Sampling | Seviye bazlı örnekleme | `utils/log_sampling.py` |
| Retention | 30/90/365 gün | `utils/log_retention.py` |
| Alertler | Eşik monitörü (opt-in) | `utils/log_alert_monitor.py` |
| Tracing | OTel (opt-in) | `utils/otel_setup.py` |
| UI | Monitoring dashboard | `/monitoring` |
| CI | PII statik tarama | `scripts/check_log_pii.py` |

---

## Ortam Değişkenleri

| Değişken | Varsayılan | Açıklama |
|----------|-----------|----------|
| `LOG_LEVEL` | `INFO` | DEBUG, INFO, WARNING, ERROR |
| `OTEL_ENABLED` | `false` | Trace propagation |
| `OTEL_EXPORTER_OTLP_ENDPOINT` | dev: `localhost:4317` | Collector adresi |
| `OTEL_CONSOLE_EXPORTER` | `false` | Console'a trace yaz |
| `LOG_ALERTS_ENABLED` | `false` | E-posta alertleri |
| `LOG_ALERT_ERROR_THRESHOLD` | `10` | Dakikadaki ERROR eşiği |
| `LOG_ALERT_CRITICAL_THRESHOLD` | `1` | Dakikadaki CRITICAL eşiği |

---

## 5N1K — Sorun Giderme Şablonu

### Sorun: trace_id loglarda sıfır (000...000)

| Soru | Cevap |
|------|-------|
| **Ne?** | OpenTelemetry trace ID aktif span olmadan loglanıyor |
| **Nerede?** | `logs/e_cuzdan.log`, `[00000000...]` |
| **Ne zaman?** | OTEL kapalı veya Flask instrumentation yok |
| **Nasıl?** | `OTEL_ENABLED=false` veya paketler kurulu değil |
| **Neden?** | Opt-in tasarım — prod'da varsayılan kapalı |
| **Kim?** | DevOps / geliştirici `.env` ile açmalı |

**Çözüm:**
```powershell
pip install -r requirements-observability.txt
# .env: OTEL_ENABLED=true
python scripts/verify_observability.py
```

---

### Sorun: OTLP connection refused (10061)

| Soru | Cevap |
|------|-------|
| **Ne?** | Trace export localhost:4317'ye bağlanamıyor |
| **Nerede?** | Uygulama stdout / OTel exporter |
| **Ne zaman?** | OTEL açık ama Collector/Jaeger çalışmıyor |
| **Nasıl?** | Docker yok veya stack başlatılmamış |
| **Neden?** | Faz 4A stack opt-in, otomatik başlamaz |
| **Kim?** | Geliştirici stack'i manuel başlatmalı |

**Çözüm (Docker varsa):**
```powershell
powershell -File scripts/start_observability.ps1
```

**Çözüm (Docker yoksa):**
```env
OTEL_ENABLED=true
OTEL_CONSOLE_EXPORTER=true
```
Uygulama otomatik olarak console exporter'a düşer (collector erişilemezse).

---

### Sorun: Monitoring ekranı boş

| Soru | Cevap |
|------|-------|
| **Ne?** | Log/stats yüklenmiyor |
| **Nerede?** | `/monitoring` |
| **Ne zaman?** | Session/auth sorunu veya log dosyası yok |
| **Nasıl?** | API 302 redirect veya 404 |
| **Neden?** | Login gerekli; credentials eksik |
| **Kim?** | Kullanıcı giriş yapmalı |

**Çözüm:** Giriş yap → `/monitoring` → DevTools Network'te `/monitoring/api/stats` 200 olmalı.

---

## Faz Durumu

| Faz | Durum |
|-----|-------|
| 1 — PII/CSRF güvenlik | ✅ |
| 2 — Request ID, filtreler, retention | ✅ |
| 3 — Alertler, CI tarama, UI | ✅ |
| 4A — Dev OTel/Jaeger (Docker opt-in) | ✅ |
| 4B — Merkezi log (Loki/ELK) | ⏸ Planlandı |
| 4C — Gelişmiş monitoring UI | ⏸ Planlandı |
| 4D — AI log analisti | ⏸ Planlandı |
| 4E — Prod rollout | ⏸ Planlandı |

---

## Log Dosyaları

| Dosya | İçerik | Retention |
|-------|--------|-----------|
| `e_cuzdan.log` | Tüm seviyeler (text) | 30 gün |
| `e_cuzdan_structured.log` | JSON | 30 gün |
| `e_cuzdan_errors.log` | ERROR+ | 90 gün |
| `e_cuzdan_errors_structured.log` | JSON ERROR+ | 90 gün |
| `e_cuzdan_security.log` | Güvenlik olayları | 365 gün |
