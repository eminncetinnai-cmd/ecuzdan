# Sprint 3.1 Report

## Domain Haritası

Portfolio
- asset_service.py
- portfolio_accounting.py
- portfolio_optimization.py
- goal_based_planning.py
- taxonomy_service.py
- advanced_allocation.py
- auto_categorization_service.py
- enhanced_categorization.py

Transactions
- transaction_service.py
- financial_ledger.py
- plan_service.py
- cash_flow_analysis.py
- comprehensive_return.py
- logbook_service.py
- catalog_service.py

Analysis
- performance_calculation.py
- benchmark_comparison.py
- risk_analysis.py
- inflation_analysis.py
- investment_performance.py
- strategy_engine.py
- strategy_service.py
- financial_health_score.py

AI
- ai_insights.py
- financial_health_score.py

Users
- auth_service.py
- session_service.py
- settings_service.py
- profile_service.py
- admin_service.py
- tenant_service.py

Reporting
- export_service.py
- dashboard_service.py
- logbook_service.py

Tenant
- tenant_service.py

Cross-cutting / Infrastructure
- db_management.py
- database_service.py
- background_service.py
- backup_encryption_service.py
- backup_validation_service.py
- financial_guide_data.py
- i18n.py
- admin_demo_data.py
- advanced_demo_data_generator.py

## Servis Bağımlılıkları

Below is the per-service dependency summary extracted from the current `services/` package.

- admin_demo_data.py
  - Domain: Cross-cutting demo support
  - Uses models: Asset, AssetSector, AssetUpdate, Category, RecurringPlan, Transaction, db
  - Uses services: financial_ledger
  - Repository usage: none

- admin_service.py
  - Domain: Users/Admin
  - Uses models: Tenant, Transaction, User, db
  - Uses services: none
  - Repository usage: none

- advanced_allocation.py
  - Domain: Portfolio / Analysis
  - Uses models: Asset, AssetSector, db
  - Uses services: none
  - Repository usage: none

- advanced_demo_data_generator.py
  - Domain: Cross-cutting demo support
  - Uses models: Asset, AssetSector, AssetType, AssetUpdate, Category, RecurringPlan, Transaction, User, db
  - Uses services: none
  - Repository usage: none

- ai_insights.py
  - Domain: AI
  - Uses models: none
  - Uses services: financial_health_score, risk_analysis, performance_calculation, benchmark_comparison, advanced_allocation, cash_flow_analysis
  - Repository usage: none

- asset_service.py
  - Domain: Portfolio
  - Uses models: none
  - Uses services: financial_ledger
  - Repository usage: CatalogRepository, FinancialRepository
  - Uses engines: financial_engine

- auth_service.py
  - Domain: Users
  - Uses models: none
  - Uses services: none
  - Repository usage: UserRepository

- auto_categorization_service.py
  - Domain: Portfolio / Transactions
  - Uses models: Category, EntityTag, Tag, Transaction, db
  - Uses services: none
  - Repository usage: none

- background_service.py
  - Domain: Infrastructure
  - Uses models: none
  - Uses services: none
  - Repository usage: none
  - External dependencies: requests, BeautifulSoup, pandas, yfinance

- backup_encryption_service.py
  - Domain: Infrastructure
  - Uses models: none
  - Uses services: none
  - Repository usage: none

- backup_validation_service.py
  - Domain: Infrastructure
  - Uses models: db
  - Uses services: backup_encryption_service
  - Repository usage: none

- benchmark_comparison.py
  - Domain: Analysis
  - Uses models: Asset, db
  - Uses services: performance_calculation
  - Repository usage: none

- cash_flow_analysis.py
  - Domain: Transactions / Analysis
  - Uses models: Transaction, db
  - Uses services: none
  - Repository usage: none

- catalog_service.py
  - Domain: Transactions / Portfolio metadata
  - Uses models: none
  - Uses services: none
  - Repository usage: CatalogRepository
  - Uses database helpers: delete_category, update_category, delete_asset_type, update_asset_type, delete_asset_sector, update_asset_sector

- comprehensive_return.py
  - Domain: Transactions
  - Uses models: Asset, Transaction, db
  - Uses services: multi_currency
  - Repository usage: none

- dashboard_service.py
  - Domain: Reporting
  - Uses models: none
  - Uses services: none
  - Repository usage: CatalogRepository, FinancialRepository
  - Uses engines: financial_engine

- database_service.py
  - Domain: Infrastructure
  - Uses models: Asset, RecurringPlan, Transaction
  - Uses services: none
  - Repository usage: none

- db_management.py
  - Domain: Infrastructure
  - Uses models: Asset, AssetSector, AssetTransaction, AssetType, AssetUpdate, BackupMetadata, Category, CategoryAssetTypeMapping, EntityTag, InvestorProfile, InvestorProfileAnswer, LogbookEntry, Payment, ProfileQuestion, RecurringPlan, StrategySettings, Tag, Tenant, TenantInvite, Transaction, User, db
  - Uses services: backup_encryption_service, backup_validation_service
  - Repository usage: none

- enhanced_categorization.py
  - Domain: Portfolio / Transactions
  - Uses models: Category, Transaction, db
  - Uses services: none
  - Repository usage: none

- export_service.py
  - Domain: Reporting
  - Uses models: none
  - Uses services: db_management
  - Repository usage: FinancialRepository, UserRepository

- financial_guide_data.py
  - Domain: Cross-cutting data support
  - Uses models: none
  - Uses services: none
  - Repository usage: none

- financial_health_score.py
  - Domain: AI / Analysis
  - Uses models: Asset, Transaction, db
  - Uses services: performance_calculation, advanced_allocation
  - Repository usage: none

- financial_ledger.py
  - Domain: Transactions
  - Uses models: Asset, AssetTransaction, AssetUpdate, Category, LogbookEntry, Payment, RecurringPlan, Transaction, db
  - Uses services: none
  - Repository usage: none
  - Uses database helpers: add_transaction, log_asset_update, add_recurring_plan, update_recurring_plan, delete_plan

- goal_based_planning.py
  - Domain: Portfolio
  - Uses models: Asset, db
  - Uses services: none
  - Repository usage: none

- i18n.py
  - Domain: Cross-cutting / Localization
  - Uses models: User, db
  - Uses services: none
  - Repository usage: none

- inflation_analysis.py
  - Domain: Analysis
  - Uses models: Asset, db
  - Uses services: investment_performance
  - Repository usage: none

- investment_performance.py
  - Domain: Analysis
  - Uses models: Asset, AssetUpdate, StrategySettings, db
  - Uses services: none
  - Repository usage: none

- logbook_service.py
  - Domain: Transactions / Reporting
  - Uses models: none
  - Uses services: none
  - Repository usage: LogbookRepository

- multi_currency.py
  - Domain: Cross-cutting / Analysis support
  - Uses models: Asset, Tenant, Transaction, User, db
  - Uses services: none
  - Repository usage: none

- performance_calculation.py
  - Domain: Analysis
  - Uses models: Asset, AssetTransaction, Transaction, db
  - Uses services: none
  - Repository usage: none

- plan_service.py
  - Domain: Transactions
  - Uses models: none
  - Uses services: financial_ledger
  - Repository usage: CatalogRepository, FinancialRepository
  - Uses engines: financial_engine
  - Uses database helpers: create_payment, get_calendar_month_data

- portfolio_accounting.py
  - Domain: Portfolio
  - Uses models: Asset, AssetTransaction, db
  - Uses services: none
  - Repository usage: none

- portfolio_optimization.py
  - Domain: Portfolio
  - Uses models: none
  - Uses services: none
  - Repository usage: none

- profile_scoring_engine.py
  - Domain: Users
  - Uses models: InvestorProfile, InvestorProfileAnswer, ProfileQuestion, db
  - Uses services: none
  - Repository usage: none

- profile_service.py
  - Domain: Users
  - Uses models: none
  - Uses services: profile_scoring_engine
  - Repository usage: ProfileRepository

- risk_analysis.py
  - Domain: Analysis
  - Uses models: Asset, AssetUpdate, db
  - Uses services: none
  - Repository usage: none

- session_service.py
  - Domain: Users
  - Uses models: none
  - Uses services: none
  - Repository usage: UserRepository

- settings_service.py
  - Domain: Users
  - Uses models: none
  - Uses services: i18n
  - Repository usage: UserRepository

- simulation_engine.py
  - Domain: Portfolio
  - Uses models: none
  - Uses services: none
  - Repository usage: none

- strategy_engine.py
  - Domain: Analysis
  - Uses models: Asset, AssetSector, StrategySettings, Transaction, db
  - Uses services: none
  - Repository usage: none
  - Uses database helpers: get_actual_cash, get_total_assets

- strategy_service.py
  - Domain: Analysis
  - Uses models: none
  - Uses services: strategy_engine
  - Repository usage: FinancialRepository, StrategyRepository

- taxonomy_service.py
  - Domain: Portfolio / Transactions metadata
  - Uses models: Asset, AssetSector, AssetType, Category, CategoryAssetTypeMapping, db
  - Uses services: none
  - Repository usage: none

- tenant_service.py
  - Domain: Tenant / Users
  - Uses models: none
  - Uses services: none
  - Repository usage: UserRepository

- transaction_service.py
  - Domain: Transactions
  - Uses models: none
  - Uses services: financial_ledger
  - Repository usage: CatalogRepository, FinancialRepository
  - Uses engines: financial_engine

## Risk Analizi

CRITICAL
- db_management.py — cross-cutting database export/import with broad model coverage and backup integration.
- background_service.py — thread/external integration risk, scraping and live feed orchestration.
- ai_insights.py — central AI orchestration hub with many downstream analysis service dependencies.
- financial_ledger.py — core transaction ledger, direct DB model mutations and broad business impact.
- export_service.py — reporting export plus database import/export surface.
- tenant_service.py — tenancy boundary and permission checks.
- settings_service.py — user settings and admin operations.

HIGH
- transaction_service.py — transaction orchestration with repository access and ledger coupling.
- plan_service.py — recurring plan / payment orchestration across finance and category repositories.
- asset_service.py — portfolio asset orchestration with repository and engine coupling.
- dashboard_service.py — reporting orchestration spanning catalog and financial repositories.
- profile_service.py — user profile orchestration with repository + scoring engine.
- strategy_service.py — strategy orchestration with repository dependencies.
- auth_service.py — user authentication and registration boundary.
- financial_health_score.py — AI support used by the AI orchestration layer.

MEDIUM
- performance_calculation.py — pure analysis but widely reused.
- benchmark_comparison.py — analysis helper used by AI and performance workflows.
- risk_analysis.py — analysis helper used by AI and portfolio risk workflows.
- inflation_analysis.py — analysis helper used by investment performance workflows.
- investment_performance.py — performance analysis with transactional model usage.
- comprehensive_return.py — returns analytics with currency support.
- cash_flow_analysis.py — transaction/cash flow analytics.
- strategy_engine.py — financial strategy engine with direct model access.
- profile_scoring_engine.py — user profile engine with database model access.
- database_service.py — DB helper service.

LOW
- session_service.py
- catalog_service.py
- logbook_service.py
- portfolio_optimization.py
- simulation_engine.py
- financial_guide_data.py
- backup_encryption_service.py
- backup_validation_service.py
- admin_demo_data.py
- advanced_demo_data_generator.py
- advanced_allocation.py
- portfolio_accounting.py
- goal_based_planning.py
- auto_categorization_service.py
- enhanced_categorization.py

## İlk Taşınacak Servisler

LOW risk services that are strong candidates for Sprint 3.2:

- session_service.py
- catalog_service.py
- logbook_service.py
- portfolio_optimization.py
- simulation_engine.py
- financial_guide_data.py
- backup_encryption_service.py
- backup_validation_service.py
- admin_demo_data.py
- advanced_demo_data_generator.py
- advanced_allocation.py
- portfolio_accounting.py
- goal_based_planning.py
- auto_categorization_service.py
- enhanced_categorization.py

These files have limited cross-domain coupling, minimal repository/service dependency chains, and are likely to be safe first movers during the modular refactor.
