# Portfolio Domain Models

Domain purpose:
- Store and track investment assets, valuation history, and portfolio transaction details.

Models targeted for migration:
- `Asset`
- `AssetUpdate`
- `AssetTransaction`

Status:
- These models have been moved in Phase 5.4 into `domain/portfolio/models/`.

Other domain dependencies:
- `AssetSector` and `AssetType` in the catalog domain for classification
- `Tenant` in shared core for tenant scoping
- `Transaction` in transactions domain via cash ledger and asset linking
- `LogbookEntry` references `Asset`

Risk level:
- Medium-High
- Asset models are central to portfolio accounting and interact with transaction flow.

Suggested migration order:
1. `shared/models`
2. `domain/catalog/models`
3. `domain/portfolio/models`
4. `domain/transactions/models`
