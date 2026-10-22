"""Simple composition root / container used as a Phase 7 scaffold.

Design goals:
- non-invasive: nothing wired automatically; routes or other code must opt-in to use container
- lazy singletons for repositories and application services
- simple override API for tests
- no external dependencies

Sprint 8.9A.2: Container modularized into bootstrap/providers/ sub-modules.
This file re-exports everything for backward compatibility.
"""
from typing import Optional

# ---------------------------------------------------------------------------
# Repository imports are performed inside methods to avoid import-time cycles.
# ---------------------------------------------------------------------------

class RepositoryProvider:
    """Provides repository instances. Lazy-singleton and overrideable for tests.

    Usage:
        providers = RepositoryProvider()
        catalog_repo = providers.catalog()

    Test override example:
        providers.set_override('catalog', FakeCatalogRepository())
    """
    def __init__(self):
        self._instances = {}
        self._overrides = {}

    def _get_or_create(self, key: str, factory):
        if key in self._overrides:
            return self._overrides[key]
        if key not in self._instances:
            self._instances[key] = factory()
        return self._instances[key]

    def set_override(self, key: str, instance):
        """Set an override instance for tests or special runtime configuration."""
        self._overrides[key] = instance
        if key in self._instances:
            del self._instances[key]

    def reset_overrides(self):
        self._overrides = {}

    # Concrete repository factory methods
    def catalog(self):
        from repositories.catalog_repository import CatalogRepository
        return self._get_or_create('catalog', CatalogRepository)

    def portfolio(self):
        from repositories.portfolio_repository import PortfolioRepository
        return self._get_or_create('portfolio', PortfolioRepository)

    def financial(self):
        from repositories.financial_repository import FinancialRepository
        return self._get_or_create('financial', FinancialRepository)

    def reporting(self):
        from repositories.reporting_repository import ReportingRepository
        return self._get_or_create('reporting', ReportingRepository)

    def user(self):
        from repositories.user_repository import UserRepository
        return self._get_or_create('user', UserRepository)

    def profile(self):
        from repositories.profile_repository import ProfileRepository
        return self._get_or_create('profile', ProfileRepository)


    def logbook(self):
        from repositories.logbook_repository import LogbookRepository
        return self._get_or_create('logbook', LogbookRepository)

    def iban(self):
        from repositories.iban_repository import IbanRepository
        return self._get_or_create('iban', IbanRepository)

    def strategy(self):
        from repositories.strategy_repository import StrategyRepository
        return self._get_or_create('strategy', StrategyRepository)

    def notification(self):
        from repositories.notification_repository import NotificationRepository
        return self._get_or_create('notification', NotificationRepository)


class DomainProvider:
    """Provides domain service instances composed from repositories.

    Usage:
        domains = DomainProvider(repositories=RepositoryProvider())
        catalog_service = domains.catalog()

    Test override example:
        domains.set_override('catalog', FakeCatalogService())
    """

    def __init__(self, repositories: Optional[RepositoryProvider] = None):
        self.repositories = repositories or RepositoryProvider()
        self._instances = {}
        self._overrides = {}

    def _get_or_create(self, key: str, factory):
        if key in self._overrides:
            return self._overrides[key]
        if key not in self._instances:
            self._instances[key] = factory()
        return self._instances[key]

    def set_override(self, key: str, instance):
        """Set an override instance for tests or special runtime configuration."""
        self._overrides[key] = instance
        if key in self._instances:
            del self._instances[key]

    def reset_overrides(self):
        """Reset all overrides."""
        self._overrides = {}

    # Concrete domain service factory methods
    def catalog(self):
        """Return CatalogService built with CatalogRepository."""
        from domain.transactions.services.catalog_service import CatalogService

        def _factory():
            return CatalogService(repository=self.repositories.catalog())

        return self._get_or_create('catalog', _factory)

    def session(self):
        """Return SessionService built with UserRepository."""
        from domain.users.services.session_service import SessionService

        def _factory():
            return SessionService(repository=self.repositories.user())

        return self._get_or_create('session_svc', _factory)

    def auth(self):
        """Return AuthService built with UserRepository."""
        from domain.users.services.auth_service import AuthService
        def _factory():
            return AuthService(repository=self.repositories.user())
        return self._get_or_create('auth_svc', _factory)

    def profile(self):
        from domain.users.services.profile_service import ProfileService
        def _factory():
            # ProfileService get_active_profile/list_history bekler — bunlar
            # ProfileRepository'de yaşar, UserRepository'de değil.
            return ProfileService(repository=self.repositories.profile())
        return self._get_or_create('profile_svc', _factory)

    def settings_svc(self):
        from domain.users.services.settings_service import SettingsService
        def _factory():
            return SettingsService(repository=self.repositories.user())
        return self._get_or_create('settings_svc', _factory)

    def admin_svc(self):
        import domain.admin.services.admin_service as admin_mod
        # admin_service uses db.session directly; return module handle
        return admin_mod



    def tenant(self):
        from domain.users.services.tenant_service import TenantService
        def _factory():
            return TenantService(repository=self.repositories.user())
        return self._get_or_create('tenant_svc', _factory)

    def dashboard(self):
        from domain.reporting.services.dashboard_service import DashboardService
        def _factory():
            return DashboardService(
                financial_repository=self.repositories.financial(),
                catalog_repository=self.repositories.catalog(),
            )
        return self._get_or_create('dashboard_svc', _factory)

    def notification(self):
        """Return NotificationService built with NotificationRepository."""
        from domain.notifications.services import NotificationService

        def _factory():
            return NotificationService(repository=self.repositories.notification())

        return self._get_or_create('notification_svc', _factory)

    def plan(self):
        """Return PlanService built with financial + catalog repositories."""
        from domain.planning.services.plan_service import PlanService

        def _factory():
            return PlanService(
                financial_repository=self.repositories.financial(),
                catalog_repository=self.repositories.catalog(),
            )

        return self._get_or_create('plan_svc', _factory)

    def logbook_svc(self):
        from domain.analysis.services.logbook_service import LogbookService
        def _factory():
            return LogbookService(repository=self.repositories.logbook())
        return self._get_or_create('logbook_svc', _factory)

    def iban_svc(self):
        from domain.analysis.services.iban_service import IbanService
        return self._get_or_create('iban_svc', IbanService)

    def strategy_svc(self):
        from domain.analysis.services.strategy_service import StrategyService
        def _factory():
            return StrategyService(
                financial_repository=self.repositories.financial(),
                # StrategySettings CRUD'u StrategyRepository'de yaşar;
                # PortfolioRepository get_settings_for_user'ı tanımıyor.
                repository=self.repositories.strategy(),
            )
        return self._get_or_create('strategy_svc', _factory)


class ApplicationProvider:
    """Provides application service instances composed from domain services.

    Usage:
        apps = ApplicationProvider(domains=DomainProvider())
        catalog_app = apps.catalog()

    Override: use domains.set_override(...) or repositories.set_override(...) before creating the application provider.
    """

    def __init__(self, domains: Optional[DomainProvider] = None, infrastructure=None):
        self.domains = domains or DomainProvider()
        self.infrastructure = infrastructure
        self._instances = {}

    def _get_or_create(self, key: str, factory):
        if key not in self._instances:
            self._instances[key] = factory()
        return self._instances[key]

    def reset_overrides(self):
        """Clear cached instances so they are recreated on next access."""
        self._instances = {}

    def session(self):
        from application.users.session_application import SessionApplicationService
        def _factory():
            return SessionApplicationService(domain_service=self.domains.session())
        return self._get_or_create('session_app', _factory)


    def catalog(self):
        """Return CatalogApplicationService built with CatalogService from DomainProvider."""
        from application.transactions.catalog_application import CatalogApplicationService

        def _factory():
            service = self.domains.catalog()
            return CatalogApplicationService(domain_service=service)

        return self._get_or_create('catalog_app', _factory)

    def reset_catalog(self):
        """Reset catalog application service cache."""
        if 'catalog_app' in self._instances:
            del self._instances['catalog_app']

    def notifications(self):
        """Return NotificationApplicationService built with NotificationService."""
        from application.notifications import NotificationApplicationService

        def _factory():
            return NotificationApplicationService(notification_service=self.domains.notification())

        return self._get_or_create('notification_app', _factory)

    def transaction_queries(self):
        from application.transactions.queries import GetTransactionPageQuery
        def _factory():
            return {
                'get_transaction_page': GetTransactionPageQuery(
                    financial_repository=self.domains.repositories.financial(),
                    catalog_repository=self.domains.repositories.catalog()
                )
            }
        return self._get_or_create('transaction_queries', _factory)

    def transaction_commands(self, outbox_port):
        from application.transactions.commands import (
            CreateTransactionCommand,
            DeleteTransactionCommand,
            UpdateTransactionCommand,
        )
        def _factory():
            return {
                'create': CreateTransactionCommand(
                    catalog_repository=self.domains.repositories.catalog(),
                    outbox=outbox_port
                ),
                'update': UpdateTransactionCommand(
                    catalog_repository=self.domains.repositories.catalog(),
                    outbox=outbox_port
                ),
                'delete': DeleteTransactionCommand(
                    outbox=outbox_port
                )
            }
        return self._get_or_create('transaction_commands', _factory)


    def portfolio(self):
        from application.portfolio.portfolio_application import PortfolioApplicationService
        from domain.portfolio.services.asset_service import AssetService

        def _factory():
            asset_service = AssetService(
                financial_repository=self.domains.repositories.financial(),
                catalog_repository=self.domains.repositories.catalog()
            )
            outbox_port = None
            if self.infrastructure:
                outbox_port = self.infrastructure.outbox()
            return PortfolioApplicationService(asset_service=asset_service, outbox=outbox_port)

        return self._get_or_create('portfolio_app', _factory)

    def users(self):
        from application.users.user_application import UserApplicationService
        def _factory():
            return UserApplicationService(
                auth_service=self.domains.auth(),
                profile_service=self.domains.profile(),
                tenant_service=self.domains.tenant(),
            )
        return self._get_or_create('users_app', _factory)

    def settings(self):
        from application.settings.settings_application import SettingsApplicationService
        def _factory():
            return SettingsApplicationService(settings_service=self.domains.settings_svc())
        return self._get_or_create('settings_app', _factory)

    def admin(self):
        from application.admin.admin_application import AdminApplicationService
        def _factory():
            return AdminApplicationService()
        return self._get_or_create('admin_app', _factory)

    def ai_insights(self):
        from application.ai.insights_application import InsightsApplicationService
        def _factory():
            from infrastructure.ai.rule_based_gateway import AIInsightsEngine
            return InsightsApplicationService(gateway=AIInsightsEngine())
        return self._get_or_create('ai_insights_app', _factory)




    def profile(self):
        from application.users.profile_application import ProfileApplicationService
        def _factory():
            return ProfileApplicationService(profile_service=self.domains.profile())
        return self._get_or_create('profile_app', _factory)

    def auth(self):
        from application.users.auth_application import AuthApplicationService
        def _factory():
            outbox_port = None
            if self.infrastructure:
                outbox_port = self.infrastructure.outbox()
            return AuthApplicationService(auth_service=self.domains.auth(), outbox=outbox_port)
        return self._get_or_create('auth_app', _factory)

    def oauth(self):
        from application.users.oauth_application_service import OAuthApplicationService
        def _factory():
            # OAuth provider catalog is resolved lazily by oauth_provider(); avoid unused eager lookup.
            # Note: OAuthApplicationService now takes a single provider instance
            # This factory will need to be called with a specific provider
            return OAuthApplicationService
        return self._get_or_create('oauth_app', _factory)


    def tenant(self):
        from application.users.tenant_application import TenantApplicationService
        def _factory():
            return TenantApplicationService(tenant_service=self.domains.tenant())
        return self._get_or_create('tenant_app', _factory)

    def dashboard(self):
        from application.reporting.dashboard_application import DashboardApplicationService
        def _factory():
            return DashboardApplicationService(dashboard_service=self.domains.dashboard())
        return self._get_or_create('dashboard_app', _factory)

    def logbook(self):
        from application.analysis.logbook_application import LogbookApplicationService
        def _factory():
            return LogbookApplicationService(logbook_service=self.domains.logbook_svc())
        return self._get_or_create('logbook_app', _factory)

    def iban(self):
        from application.analysis.iban_application import IbanApplicationService
        def _factory():
            return IbanApplicationService(
                iban_domain_service=self.domains.iban_svc(),
            )
        return self._get_or_create('iban_app', _factory)

    def analysis(self):
        from application.analysis.analysis_application import AnalysisApplicationService
        from domain.analysis.services.inflation_analysis import InflationAnalyzer
        from domain.analysis.services.risk_analysis import RiskAnalyzer
        def _factory():
            return AnalysisApplicationService(
                inflation_analyzer=InflationAnalyzer(),
                risk_analyzer=RiskAnalyzer()
            )
        return self._get_or_create('analysis_app', _factory)

    def strategy(self):
        from application.analysis.strategy_application import StrategyApplicationService
        def _factory():
            return StrategyApplicationService(strategy_service=self.domains.strategy_svc())
        return self._get_or_create('strategy_app', _factory)


class InfrastructureProvider:
    """Provides infrastructure service instances. Lazy-singleton."""

    def __init__(self):
        self._instances = {}

    def _get_or_create(self, key: str, factory):
        if key not in self._instances:
            self._instances[key] = factory()
        return self._instances[key]

    def oauth_providers(self):
        """Provide OAuth providers."""
        from config import Config
        from infrastructure.auth.google_provider import GoogleOAuthProvider
        config = Config.from_env()

        def _factory():
            providers = {}
            if config.GOOGLE_CLIENT_ID and config.GOOGLE_CLIENT_SECRET:
                providers['google'] = GoogleOAuthProvider(
                    client_id=config.GOOGLE_CLIENT_ID,
                    client_secret=config.GOOGLE_CLIENT_SECRET
                )
            return providers
        return self._get_or_create('oauth_providers', _factory)

    def oauth_provider(self, provider_name: str = 'google'):
        """Provide a specific OAuth provider instance.

        Args:
            provider_name: Name of the provider (e.g., 'google')

        Returns:
            OAuthProvider instance or None if not configured
        """
        from config import Config
        from infrastructure.auth.google_provider import GoogleOAuthProvider
        config = Config.from_env()

        def _factory():
            if provider_name == 'google' and config.GOOGLE_CLIENT_ID and config.GOOGLE_CLIENT_SECRET:
                return GoogleOAuthProvider(
                    client_id=config.GOOGLE_CLIENT_ID,
                    client_secret=config.GOOGLE_CLIENT_SECRET
                )
            return None
        return self._get_or_create(f'oauth_provider_{provider_name}', _factory)

    def background(self):
        from infrastructure.background.background_service import BackgroundService
        def _factory():
            return BackgroundService()
        return self._get_or_create('background_svc', _factory)

    def db_management(self):
        import infrastructure.database.management as db_management
        return db_management

    def backup_encryption(self):
        import infrastructure.backup.encryption as encryption
        return encryption

    def backup_validation(self):
        import infrastructure.backup.validation as validation
        return validation

    def event_bus(self):
        """Provide the central LocalEventBus."""
        from infrastructure.events.local_event_bus import LocalEventBus
        def _factory():
            return LocalEventBus()
        return self._get_or_create('event_bus', _factory)

    def async_event_bus(self):
        """Provide the central AsyncLocalEventBus."""
        from infrastructure.events.async_local_event_bus import AsyncLocalEventBus
        def _factory():
            return AsyncLocalEventBus()
        return self._get_or_create('async_event_bus', _factory)

    def outbox(self):
        """Provide the OutboxPort adapter (SQLAlchemy-backed)."""
        from infrastructure.database.outbox_adapter import SqlAlchemyOutboxAdapter
        def _factory():
            return SqlAlchemyOutboxAdapter()
        return self._get_or_create('outbox', _factory)

    def tracer(self, service_name: str = "e_cuzdan"):
        """Setup and return the OpenTelemetry tracer provider (idempotent)."""
        from infrastructure.observability.tracing import setup_tracing
        def _factory():
            return setup_tracing(service_name=service_name)
        return self._get_or_create('tracer_provider', _factory)

# Top-level container instance for convenience; tests or bootstrapping code may replace this.
container = {
    'repositories': RepositoryProvider(),
    'domains': None,  # lazily created below
    'applications': None,  # lazily created below
    'infrastructure': None,  # lazily created below
}


class Container:
    """Composition root. Wires all providers together."""

    def __init__(self):
        self.repositories = RepositoryProvider()
        self.domain = DomainProvider(repositories=self.repositories)
        self.infrastructure = InfrastructureProvider()
        self.applications = ApplicationProvider(domains=self.domain, infrastructure=self.infrastructure)

    @property
    def domains(self):
        return self.domain

    def reset_overrides(self):
        self.repositories.reset_overrides()
        self.domain.reset_overrides()
        self.applications.reset_overrides()


container = Container()


def get_container() -> Container:
    """Return the global container singleton."""
    return container


def reset_container():
    """Reset all overrides on the global container (useful for tests)."""
    container.reset_overrides()
