# Transactions Domain Models

Domain purpose:
- Represent core cash flow events, recurring plans, payments, and logbook entries.

Models targeted for migration:
- `Transaction`
- `RecurringPlan`
- `Payment`
- `LogbookEntry`

Other domain dependencies:
- `Tenant` and `User` from shared/user domains
- `Asset` from portfolio domain for logbook and asset-linked entries
- `Category` from catalog for transaction classification
- `Payment` depends on `Transaction` and `RecurringPlan`

Risk level:
- Critical
- This domain is the ledger backbone and has many cross-domain references.

Suggested migration order:
1. `shared/models`
2. `domain/tenant/models`
3. `domain/users/models`
4. `domain/portfolio/models`
5. `domain/transactions/models`
