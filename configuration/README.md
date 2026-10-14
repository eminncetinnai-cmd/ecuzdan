# configuration/ — Ortam ve Paket Bağımlılık Yönetimi

Bu dizin, E-Cüzdan projesinin farklı çalışma ortamlarına (Development, Production, E2E, Observability) ait Python paket bağımlılıklarını ve kilit (lock) dosyalarını barındırır.

## Dizin Yapısı:
- **`dependencies/`**:
  - `requirements.txt`: Ana çalışma zamanı paketleri (Kök dizindeki `requirements.txt` burayı referans alır).
  - `requirements-dev.txt`: Test, linter, Mypy ve geliştirici araçları.
  - `requirements-production.txt`: Canlı ortam optimize bağımlılık seti.
  - `requirements-e2e.txt`: Playwright ve uçtan uca test bağımlılıkları.
  - `requirements-observability.txt`: OpenTelemetry, Prometheus ve izleme paketleri.
  - `*-lock.txt` & `*-constraints.txt`: Tekrarlanabilir (deterministic) build için kilitlenmiş tam sürümler.
