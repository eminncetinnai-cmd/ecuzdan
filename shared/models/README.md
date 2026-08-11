# Shared Models

Domain purpose:
- Host core cross-domain infrastructure models and shared tenant context.

Models targeted for migration:
- `Tenant`
- `BackupMetadata`

Other domain dependencies:
- `User` from user domain
- `Tenant` is referenced by almost every business model in the codebase
- `BackupMetadata` is infrastructure-level and cross-domain

Risk level:
- High
- Shared models must be established first to avoid import cycles and maintain tenant scoping.

Suggested migration order:
1. `shared/models`
2. `domain/tenant/models`
3. `domain/catalog/models`
4. `domain/users/models`
