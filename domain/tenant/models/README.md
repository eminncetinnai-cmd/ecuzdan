# Tenant Domain Models

Domain purpose:
- Manage multi-tenant boundaries, tenant metadata, and tenant lifecycle.

Models targeted for migration:
- `Tenant`

Other domain dependencies:
- referenced by most business models including `User`, `Asset`, `Transaction`, `RecurringPlan`, `Payment`, `Tag`, `CategoryAssetTypeMapping`, `AssetTransaction`, `BackupMetadata`, `InvestorProfile`, `LogbookEntry`

Risk level:
- High
- `Tenant` is the core shared model for multi-tenancy and must be migrated carefully.

Suggested migration order:
1. `shared/models`
2. `domain/tenant/models`
3. then catalog, portfolio, transactions, and planning domains
