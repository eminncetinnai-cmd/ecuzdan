Application Layer Standard

- Each ApplicationService is a class named <BoundedName>ApplicationService.
- Constructor signature accepts domain services and adapters as optional args.
  e.g. def __init__(self, portfolio_service=None, reporting_service=None, **kwargs)
- ApplicationService methods are use-case oriented (e.g., rebalance_portfolio).
- No business logic inside ApplicationService; only orchestration and cross-cutting concerns.
- Support hooks: before_execute(context) and after_execute(context, result).
- ApplicationService may use repository contracts but should not directly perform complex SQL or domain rule evaluation.
