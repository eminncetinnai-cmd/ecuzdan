# `scripts/` — Operasyonel ve Mimari Otomasyon Betikleri

Bu dizin, E-Cüzdan projesinin kalite kapıları, veritabanı bakım araçları, E2E test simülatörleri ve geliştirici araçlarını içerir.

---

## 🧭 Betik Envanteri ve Sorumluluk Haritası

### 1. Kalite, Mimari ve Güvenlik Kapıları (Zorunlu Kapılar)
| Betik | Çalıştırma | Amacı |
|-------|------------|-------|
| `check_design_system.py` | `python scripts/check_design_system.py --ratchet` | Şablonlarda inline CSS, geçersiz renk ve tasarım token ihlallerini denetler. |
| `check_type_annotations.py` | `python scripts/check_type_annotations.py` | Proje genelinde statik tip denetimi (Mypy) yapar. |
| `governance/run_architecture_gate.ps1` | `powershell -ExecutionPolicy Bypass -File scripts/governance/run_architecture_gate.ps1 -Mode BLOCK` | Katman ihlallerini, izinsiz kök dosyalarını ve bağımlılık kurallarını denetler. |
| `preflight_check.py` | `python scripts/preflight_check.py` | 54 Jinja şablonunu derler, tüm uç noktalara GET isteği gönderir ve 0 hata doğrulaması yapar. |
| `run_ledger_watchdog.py` | `python scripts/run_ledger_watchdog.py` | Çift taraflı defter dengesi, SHA-256 zinciri ve bakiye mutabakatını denetler. |
| `check_log_pii.py` | `python scripts/check_log_pii.py` | Log dosyalarında hassas veri (şifre, token, PII) sızıntısını denetler. |
| `fuzz_tenant_isolation.py` | `python scripts/fuzz_tenant_isolation.py` | Multi-tenant veri izolasyonunu fuzzer ile test eder (IDOR koruması). |
| `verify_all.py` | `python scripts/verify_all.py` | Tüm kapıları ve test paketini tek seferde yürüten ana doğrulayıcıdır. |

### 2. Veritabanı ve Veri Yönetimi
| Betik | Amacı |
|-------|-------|
| `verify_database_schema.py` | SQLite indeksleri, PRAGMA ayarları ve şema versiyonunu doğrular. |
| `seed_standard_categories.py` | Standart gelir/gider kategorilerini başlatır. |
| `seed_profile_questions.py` | Yatırımcı profili anket sorularını doldurur. |
| `backfill_historical_ledger.py` | Eski işlemlerin muhasebe defterine (ledger) kaydını geriye dönük işler. |
| `maintenance.py` / `run_maintenance.ps1` | VACUUM, ANALYZE ve indeks optimizasyonu yapar. |
| `clean_caches.py` | `python scripts/clean_caches.py` \| Güvenli önbellek, bytecode ve snapshot temizliği yapar. |

### 3. E2E ve Yaşam Döngüsü Simülasyonu
| Betik | Amacı |
|-------|-------|
| `run_complete_user_lifecycle.py` | Kayıt, giriş, işlem ekleme, portföy ve raporlama döngüsünü baştan sona simüle eder. |
| `run_e2e.ps1` | Web tarayıcısı üzerinden E2E senaryolarını koşturur. |
| `run_authenticated_e2e_preflight.ps1` | Oturum açmış kullanıcı için preflight smoke testini koşturur. |

### 4. Geliştirici Kancaları ve Gözlemlenebilirlik
| Betik | Amacı |
|-------|-------|
| `install_hooks.py` / `install_git_hooks.ps1` | Git pre-commit ve pre-push kancalarını yerel `.git/hooks/` dizinine yükler. |
| `start_observability.ps1` / `stop_observability.ps1` | Docker üzerinden Loki/Prometheus/Grafana yığınını başlatır/durdurur. |
