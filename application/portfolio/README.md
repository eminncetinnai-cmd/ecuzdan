Portfolio Application Package

Purpose:
- Orchestration for portfolio-related use-cases (rebalance, import/export, holdings management).

Planned models:
- Asset, Portfolio, AssetHolding, AssetType

Dependencies:
- domain.portfolio services
- repositories.portfolio repository
- shared/db

Risk level: LOW (portfolio models already migrated and repository layer exists)

Migration order: P5.4 already moved catalog; portfolio application scaffolding created in P6.2 as an orchestration layer.
