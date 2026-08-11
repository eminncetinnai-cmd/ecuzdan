# Catalog Domain Models

Domain purpose:
- Manage categories, asset classification, tagging, and catalog mappings.

Models targeted for migration:
- `Category`
- `AssetType`
- `AssetSector`

Models remaining in later waves:
- `CategoryAssetTypeMapping`
- `Tag`
- `EntityTag`

Other domain dependencies:
- `Tenant` for tenant-specific catalog objects
- `Asset` and `Transaction` for category assignment and tagging operations

Risk level:
- Medium
- Catalog models are important for classification but are relatively isolated from ledger core.

Suggested migration order:
1. `shared/models`
2. `domain/catalog/models`
3. `domain/portfolio/models`
4. `domain/transactions/models`
