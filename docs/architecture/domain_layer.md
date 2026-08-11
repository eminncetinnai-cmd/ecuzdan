Domain Layer Guidance

- Domain services contain business rules and validations. Keep them pure from framework concerns.
- Domain services depend on repository contracts for persistence.
- Domain models should live in domain/<bounded>/models.py or shared/models and use shared/db.py for SQLAlchemy.
- Keep domain services side-effect minimal; prefer returning value objects that Application can persist or handle.
