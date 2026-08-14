# Business Scenario Test Plan

## Overview
This document outlines the critical end-to-end business scenarios for financial operations that should be tested to ensure production readiness.

## Priority Business Scenarios

### 1. Monthly Budget Cycle (High Priority)
**Description:** Complete monthly income and expense workflow

**Test Steps:**
1. User receives salary income transaction
2. User records recurring expenses (rent, utilities, subscriptions)
3. User records one-time expenses (groceries, entertainment)
4. System calculates monthly cash flow
5. System updates financial health metrics (liquidity, savings rate)
6. Dashboard reflects accurate monthly summary

**Success Criteria:**
- Income transactions correctly increase cash balance
- Expense transactions correctly decrease cash balance
- Monthly cash flow calculation is accurate
- Financial health metrics update correctly
- Dashboard shows real-time data

**Files Involved:**
- `routes/transactions.py` - Transaction creation
- `engines/financial_engine.py` - Cash flow analysis
- `routes/dashboard.py` - Dashboard display
- `repositories/financial_repository.py` - Data persistence

---

### 2. Investment Lifecycle (High Priority)
**Description:** Complete asset purchase, valuation update, and sale workflow

**Test Steps:**
1. User creates asset position (e.g., stock purchase)
2. System creates corresponding cash transaction (outflow)
3. User updates asset valuation
4. System records valuation event
5. User sells portion of asset
6. System records sale transaction (inflow)
7. System calculates realized profit/loss
8. Investment performance metrics update

**Success Criteria:**
- Asset creation reduces cash balance correctly
- Valuation updates are recorded with timestamps
- Partial sales calculate correct profit/loss
- Realized cash from sales is preserved when asset is deleted
- Investment performance (ROI, real ROI) is accurate

**Files Involved:**
- `domain/transactions/services/financial_ledger.py` - Asset operations
- `domain/portfolio/services/investment_performance.py` - Performance calculations
- `routes/assets.py` - Asset management UI
- `repositories/financial_repository.py` - Data persistence

---

### 3. Recurring Plan Management (High Priority)
**Description:** Creation of recurring payment plans and payment execution

**Test Steps:**
1. User creates recurring plan (e.g., loan installment)
2. System generates future transactions
3. User makes payment for installment
4. System marks transaction as paid
5. System updates remaining installments
6. User deletes plan
7. System cleans up related transactions

**Success Criteria:**
- Plan creation generates correct number of transactions
- Payment links to correct plan transaction
- Installment numbers are sequential
- Plan deletion removes all related transactions
- Rolling transaction generation works for infinite plans

**Files Involved:**
- `domain/transactions/services/financial_ledger.py` - Plan operations
- `repositories/financial_repository.py` - Payment creation
- `routes/plans.py` - Plan management UI

---

### 4. Multi-Currency Operations (Medium Priority)
**Description:** Financial operations across different currencies

**Test Steps:**
1. User records income in USD
2. User records expense in EUR
3. User creates asset in BTC
4. System converts to base currency for reporting
5. Dashboard shows multi-currency summary
6. Currency precision is maintained

**Success Criteria:**
- Currency symbols display correctly
- Decimal precision is appropriate per currency (2 for fiat, 8 for crypto)
- Currency conversions are accurate
- Multi-currency totals are calculated correctly

**Files Involved:**
- `shared/money.py` - Currency handling
- `shared/currency_precision.py` - Precision management
- `engines/financial_engine.py` - Currency conversion

---

### 5. Financial Health Analysis (Medium Priority)
**Description:** Comprehensive financial health assessment

**Test Steps:**
1. System analyzes user's complete financial data
2. Calculates liquidity ratio
3. Calculates debt ratio
4. Calculates savings rate
5. Calculates sustainability score
6. Generates financial score (0-100)
7. Provides recommendations based on flags

**Success Criteria:**
- All financial metrics are calculated correctly
- Flags are raised for critical issues (low liquidity, high debt)
- Recommendations are appropriate
- Financial score is within valid range
- Analysis is consistent across multiple runs

**Files Involved:**
- `engines/financial_engine.py` - Financial analysis
- `routes/analysis.py` - Analysis display

---

### 6. Data Integrity & Rollback (High Priority)
**Description:** Ensuring data consistency and rollback capabilities

**Test Steps:**
1. User creates complex transaction (asset with cash link)
2. System fails during creation (simulated error)
3. System rolls back all changes
4. No partial data remains in database
5. User can retry operation successfully

**Success Criteria:**
- Rollback removes all related data
- No orphaned records remain
- Database integrity is maintained
- Retry succeeds after rollback

**Files Involved:**
- `domain/transactions/services/financial_ledger.py` - Transaction management
- `repositories/base.py` - Database operations
- `models.py` - Data models

---

## Existing Integration Tests

### Current Coverage
- ✅ `test_portfolio_integration.py` - Portfolio analysis with mock assets
- ✅ `test_final_integration.py` - Component stability testing (3 consecutive runs)
- ✅ `test_strategy_integration.py` - Strategy module integration
- ✅ `test_settings_integration.py` - Settings API integration
- ✅ `test_profile_api_integration.py` - Profile API integration
- ✅ `test_notification_integration.py` - Notification system integration

### Gaps
- ❌ No end-to-end monthly budget cycle test
- ❌ No complete investment lifecycle test
- ❌ No recurring plan payment execution test
- ❌ No multi-currency workflow test
- ❌ No financial health analysis integration test
- ❌ No data integrity rollback test

## Implementation Priority

### Phase 1 (Immediate - Critical Financial Workflows)
1. Monthly Budget Cycle test
2. Investment Lifecycle test
3. Recurring Plan Management test
4. Data Integrity & Rollback test

### Phase 2 (Short-term - Enhanced Coverage)
5. Multi-Currency Operations test
6. Financial Health Analysis test

## Test Structure Recommendations

### Location
Create new integration test file: `tests/integration/test_financial_workflows.py`

### Fixture Requirements
- Full app context with database
- Authenticated user session
- Pre-populated test data (categories, sectors)
- Mock market data service for investment tests

### Test Organization
```python
class TestMonthlyBudgetWorkflow:
    """Complete monthly budget cycle tests"""
    
class TestInvestmentLifecycle:
    """Complete investment lifecycle tests"""
    
class TestRecurringPlanWorkflow:
    """Recurring plan management tests"""
    
class TestDataIntegrity:
    """Data integrity and rollback tests"""
```

## Success Metrics

- All Phase 1 scenarios implemented and passing
- Integration tests run in CI/CD pipeline
- Tests complete within reasonable time (< 5 minutes)
- No flaky tests (consistent results across runs)
- Coverage of critical financial workflows ≥ 80%

## Notes

- Business scenario tests should use real database (in-memory SQLite for CI)
- Tests should clean up after themselves (rollback transactions)
- Tests should be independent (can run in any order)
- Tests should be deterministic (no reliance on external services)
