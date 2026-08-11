# User Domain Models

Domain purpose:
- User authentication, authorization, tenant membership, and user-level preferences.

Models targeted for migration:
- `User`
- `TenantInvite`
- `StrategySettings`

Other domain dependencies:
- `Tenant` (shared core)
- `BackupMetadata` may reference user/audit data in shared infrastructure
- `LogbookEntry` and `InvestorProfile` may reference users through business logic

Risk level:
- Medium
- This domain is central to auth and access control, but it has fairly contained model relationships.

Suggested migration order:
1. `shared/models` (Tenant core)
2. `domain/users/models`
3. `domain/transactions/models` and `domain/planning/models` after user references are isolated
