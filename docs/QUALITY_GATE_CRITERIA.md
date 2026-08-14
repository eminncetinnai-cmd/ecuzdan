# E-Cüzdan Quality Gate Criteria

## Production Deployment Quality Gates

Bu kriterler production'a gitmeden önce sağlanmalıdır.

### Coverage Targets

| Metric | Target | Current | Status |
|--------|--------|---------|--------|
| Overall Line Coverage | ≥90% | 24% | 🔴 Below Target |
| Critical Financial Line Coverage | ≥55% | ~70% (weighted avg) | ✅ Above Target |
| Overall Branch Coverage | ≥55% | TBD | 🔴 Below Target |
| Critical Branch Coverage | ≥55% | TBD | 🔴 Below Target |

### Critical Financial Modules

Bu modüller için ≥55% coverage hedeflenir:

- `shared/money.py` - Para birimi ve bakiye işlemleri ✅ **96%**
- `shared/currency_precision.py` - Para birimi hassasiyeti ✅ **100%**
- `engines/financial_engine.py` - Finansal hesaplama motoru (helper functions tested)
- `domain/transactions/services/financial_ledger.py` - Finansal defter ✅ **comprehensive tests (16 tests)**
- `domain/portfolio/services/investment_performance.py` - Yatırım performansı ✅ **comprehensive regression tests (16 tests)**
- `repositories/financial_repository.py` - Finansal veri katmanı ✅ **35% (via ledger tests)**
- `repositories/portfolio_repository.py` - Portföy veri katmanı (0%)
- `models.py` - Veri modelleri (88-90%)

### Test Quality Gates

| Metric | Target | Current | Status |
|--------|--------|---------|--------|
| Skipped Tests | <30 | 20 | ✅ Within Limit |
| Skipped with Legitimate Reason | 100% | 100% | ✅ All Legitimate |
| Failed Tests | 0 | 0 | ✅ No Failures |
| Total Tests | - | 2,502 | ✅ |

### Skipped Test Categories

**A - Meşru Skip (8 adet):**
- `test_admin_demo_data.py`: 2 test - DEPRECATED, new orchestrator used
- `test_demo_data_orchestrator_unit.py`: 2 test - Database context required
- `test_event_bus.py`: 2 test - OpenTelemetry module required
- `test_strategy_integration.py`: 2 test - CSRF verification pending

**B - Geçici Skip (12 adet):**
- `test_strategy_integration.py`: 9 test - Non-existent API routes (to be removed)
- `test_notification_rules.py`: 4 test - Application context setup required
- `test_profile_services.py`: 1 test - Complex integration test setup

### Priority Order for Coverage Improvement

1. **P0 - Critical Financial (0% coverage):**
   - `shared/money.py` (0%)
   - `shared/currency_precision.py` (0%)

2. **P1 - Data Layer (10-27% coverage):**
   - `repositories/financial_repository.py` (10%)
   - `repositories/portfolio_repository.py` (0-27%)

3. **P2 - Business Logic:**
   - `engines/financial_engine.py` (TBD)
   - `domain/transactions/services/financial_ledger.py` (TBD)
   - `domain/portfolio/services/investment_performance.py` (TBD)

### Business Scenario Coverage Requirements

Finansal işlemler için şu senaryolar test edilmeli:

**Yatırım İşlemleri:**
- Alış
- İkinci alış (ortalama maliyet hesaplama)
- Fiyat değişimi
- Gerçekleşmemiş kâr
- Kısmi satış
- Gerçekleşmiş kâr
- Kalan pozisyon

**Gelir/Gider:**
- Pozitif gelir
- Negatif gider
- Sıfır değer
- Para birimi dönüşümü
- Yuvarlama

**Bakiye Hesaplama:**
- Toplam varlık
- Toplam borç
- Net değer
- Para birimi bazında hesaplama

### Quality Gate Enforcement

CI/CD pipeline'da şu kontroller yapılmalı:

```bash
# Coverage check
pytest --cov=. --cov-branch --cov-fail-under=90

# Branch coverage check for critical modules
pytest --cov=shared/money --cov-branch --cov-fail-under=55
pytest --cov=shared/currency_precision --cov-branch --cov-fail-under=55

# Skipped test limit check
pytest --co -q | grep "SKIPPED" | wc -l  # Should be < 30

# Failed test check
pytest --maxfail=1  # Fail immediately on first failure
```

### Notes

- Branch coverage line coverage'dan daha önemlidir finansal kodda
- %100 coverage ≠ %100 güvenilirlik
- Test kalitesi > Coverage yüzdesi
- Business scenario coverage > Line coverage
