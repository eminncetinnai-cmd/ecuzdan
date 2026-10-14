from typing import Optional

from .domain_provider import DomainProvider


class ApplicationProvider:
    """Provides application service instances composed from domain services.

    Usage:
        apps = ApplicationProvider(domains=DomainProvider())
        catalog_app = apps.catalog()

    Override: use domains.set_override(...) or repositories.set_override(...) before creating the application provider.
    """

    def __init__(self, domains: Optional[DomainProvider] = None):
        self.domains = domains or DomainProvider()
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

    def portfolio(self):
        from application.portfolio.portfolio_application import PortfolioApplicationService
        from domain.portfolio.services.asset_service import AssetService

        def _factory():
            asset_service = AssetService(
                financial_repository=self.domains.repositories.financial(),
                catalog_repository=self.domains.repositories.catalog()
            )
            return PortfolioApplicationService(asset_service=asset_service)

        return self._get_or_create('portfolio_app', _factory)

    def notifications(self):
        from application.notifications.notification_application import NotificationApplicationService
        from domain.notifications.services.notification_service import NotificationService
        def _factory():
            notification_service = NotificationService(repository=self.domains.repositories.notification())
            return NotificationApplicationService(notification_service=notification_service)
        return self._get_or_create('notifications_app', _factory)

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
            return AuthApplicationService(auth_service=self.domains.auth())
        return self._get_or_create('auth_app', _factory)


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

    def strategy(self):
        from application.analysis.strategy_application import StrategyApplicationService
        def _factory():
            return StrategyApplicationService(strategy_service=self.domains.strategy_svc())
        return self._get_or_create('strategy_app', _factory)


