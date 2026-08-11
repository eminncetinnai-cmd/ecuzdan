Application Layer (Clean Architecture) - Overview

- Routes (Flask blueprints) should call Application services (use-case oriented).
- Application services orchestrate Domain services and Repository operations.
- Domain services contain business rules and validation.
- Repositories provide persistence contracts and implementations.
- Models are domain entities (SQLAlchemy declarative). shared/db.py should be the single source for the SQLAlchemy registry.

Key rule: Routes -> Application -> Domain -> Repository -> Models -> DB
