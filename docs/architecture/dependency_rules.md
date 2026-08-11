Dependency Rules

- Do not allow Domain -> Application imports. Domain is lower-level than Application.
- Routes must prefer calling Application services when they exist.
- Repositories expose contracts (interfaces) that Domain services depend on.
- Models must not import Application modules.
- Use dependency injection (constructor arguments) for Application services to avoid import cycles.

Enforcement: add a static lint or CI check to flag forbidden import directions.
