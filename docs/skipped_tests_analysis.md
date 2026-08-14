# Skipped Tests Analysis

## Summary
Total skipped tests: 124

## Categories

### 1. Missing Dependencies (opentelemetry) - ~15 tests
**Files:**
- `unit/infrastructure/test_observability.py` (11 tests)
- `unit/test_tracing.py` (10 tests)
- `unit/test_event_bus.py` (2 tests)
- `unit/test_logging_config.py` (2 tests)

**Reason:** `opentelemetry` module not installed or not available

**Can we fix?** YES - Install opentelemetry dependencies
```bash
pip install opentelemetry-api opentelemetry-sdk opentelemetry-instrumentation
```

**Priority:** HIGH - These are observability tests that should work

---

### 2. Unimplemented Features/Routes - ~10 tests
**Files:**
- `integration/test_strategy_integration.py` (7 tests)
  - `/strategy/api/simulation` not implemented
  - `/strategy/api/real_yield` not implemented
  - `/strategy/api/rollback` not implemented
  - `StrategyService.run_monte_carlo_simulation` not implemented
  - `StrategyService.calculate_real_yield` not implemented

**Reason:** Features not yet implemented in the codebase

**Can we fix?** NO - Requires feature implementation first

**Priority:** LOW - These are future features

---

### 3. Complex Mocking Requirements - ~30 tests
**Files:**
- `unit/infrastructure/test_outbox_processor.py` (4 tests)
- `unit/test_audit.py` (1 test)
- `unit/test_base_repository.py` (2 tests)
- `unit/test_financial_db_service.py` (1 test)
- `integration/repositories/test_reporting_repository.py` (5 tests)
- `integration/repositories/test_user_repository.py` (2 tests)
- `integration/infrastructure/test_management.py` (5 tests)
- `integration/infrastructure/test_tenant_factory.py` (1 test)

**Reason:** Tests require complex SQLAlchemy mocking, threading, or database context

**Can we fix?** PARTIALLY - Some can be fixed with better fixtures, others are inherently complex

**Priority:** MEDIUM - These tests are valuable but complex to implement

---

### 4. Application Context Requirements - ~20 tests
**Files:**
- `unit/test_notification_rules.py` (4 tests)
- `integration/infrastructure/test_i18n.py` (4 tests)
- `unit/test_profile_services.py` (1 test)

**Reason:** Tests require Flask application context which is complex to set up in unit tests

**Can we fix?** YES - Use `app.test_request_context()` or move to integration tests

**Priority:** MEDIUM - These tests can be fixed with proper fixtures

---

### 5. Deprecated Functionality - ~2 tests
**Files:**
- `integration/test_admin_demo_data.py` (2 tests)

**Reason:** Old admin_demo_data functions deprecated in favor of DemoDataOrchestrator

**Can we fix?** NO - These are intentionally deprecated

**Priority:** NONE - Should remain skipped

---

### 6. Integration Test Complexity - ~15 tests
**Files:**
- `unit/demo/test_demo_data_orchestrator_unit.py` (2 tests)
- `unit/test_logbook_repository.py` (4 tests)
- `unit/test_format_utils.py` (2 tests)
- `integration/test_notification_integration.py` (all tests)

**Reason:** Tests better suited for integration tests or require full database setup

**Can we fix?** PARTIALLY - Move to integration tests or improve fixtures

**Priority:** LOW - These are architectural decisions

---

### 7. Mock Verification Issues - ~4 tests
**Files:**
- `unit/routes/test_categories_routes.py` (2 tests)
- `unit/test_categories_routes.py` (1 test)

**Reason:** Mock service call verification not working with current implementation

**Can we fix?** YES - Fix the mock assertions or test approach

**Priority:** MEDIUM - These are test implementation issues

---

### 8. Missing Standard Categories - ~3 tests
**Files:**
- `integration/test_demo_data_generation.py` (3 tests)

**Reason:** Demo data generation requires standard categories in test tenant

**Can we fix?** YES - Seed standard categories in test fixtures

**Priority:** MEDIUM - Requires fixture setup

---

### 9. Dangerous Operations - ~1 test
**Files:**
- `integration/repositories/test_user_repository.py` (1 test)

**Reason:** Global reset operation - dangerous to test

**Can we fix?** NO - Should remain skipped for safety

**Priority:** NONE - Safety concern

---

## Recommendations

### Immediate Actions (High Priority)
1. **Install opentelemetry dependencies** to enable ~15 observability tests
2. **Fix mock verification issues** in categories routes tests (~4 tests)
3. **Seed standard categories** in test fixtures for demo data tests (~3 tests)

### Medium Priority
4. **Add Flask context fixtures** for application context tests (~20 tests)
5. **Improve DB mocking** for repository tests (~10 tests)

### Low Priority
6. **Move unit tests to integration tests** where appropriate (~15 tests)
7. **Document unimplemented features** for strategy tests (~10 tests)

### No Action Needed
8. Deprecated tests (2 tests)
9. Dangerous operation tests (1 test)
10. Unimplemented feature tests (10 tests) - document as TODO

## Estimated Impact
- **High priority fixes:** ~22 tests could be enabled
- **Medium priority fixes:** ~30 tests could be enabled
- **Total potential improvement:** ~52 tests (42% of skipped tests)
