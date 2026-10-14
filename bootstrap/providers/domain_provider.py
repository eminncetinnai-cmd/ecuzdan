from typing import Optional

from .repository_provider import RepositoryProvider


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

        return self._get_or_create('session', _factory)

    def auth(self):
        from domain.users.services.auth_service import AuthService
        def _factory():
            return AuthService(repository=self.repositories.user())
        return self._get_or_create('auth_svc', _factory)

    def profile(self):
        from domain.users.services.profile_service import ProfileService
        def _factory():
            return ProfileService(repository=self.repositories.user())
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

    def logbook_svc(self):
        from domain.analysis.services.logbook_service import LogbookService
        def _factory():
            return LogbookService(repository=self.repositories.logbook())
        return self._get_or_create('logbook_svc', _factory)


    def strategy_svc(self):
        from domain.analysis.services.strategy_service import StrategyService
        def _factory():
            return StrategyService(
                financial_repository=self.repositories.financial(),
                repository=self.repositories.portfolio()
            )
        return self._get_or_create('strategy_svc', _factory)


