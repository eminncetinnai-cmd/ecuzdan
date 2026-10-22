
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

    def notification(self):
        from repositories.notification_repository import NotificationRepository
        return self._get_or_create('notification', NotificationRepository)

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
