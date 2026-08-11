# Planning Domain Models

Domain purpose:
- Capture investor profile, planning questionnaire, and planning-related metadata.

Models targeted for migration:
- `InvestorProfile`
- `InvestorProfileAnswer`
- `ProfileQuestion`

Other domain dependencies:
- `Tenant` and `User` from shared/user domains
- `StrategySettings` is planning-adjacent but currently remains in the user domain due to user-specific behavior

Risk level:
- Medium
- The planning models are isolated, but they depend on shared tenant and user context.

Suggested migration order:
1. `shared/models`
2. `domain/tenant/models`
3. `domain/users/models`
4. `domain/planning/models`
