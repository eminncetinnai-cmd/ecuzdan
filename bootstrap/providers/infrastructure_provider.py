
class InfrastructureProvider:
    """Provides infrastructure service instances. Lazy-singleton."""

    def __init__(self):
        self._instances = {}

    def _get_or_create(self, key: str, factory):
        if key not in self._instances:
            self._instances[key] = factory()
        return self._instances[key]

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

# Top-level container instance for convenience; tests or bootstrapping code may replace this.
container = {
    'repositories': RepositoryProvider(),
    'domains': None,  # lazily created below
    'applications': None,  # lazily created below
    'infrastructure': None,  # lazily created below
}


def get_container():
    """Return a simple container object with .repositories, .domains, .applications, and .infrastructure attributes.

    The providers are created lazily so tests can set overrides first:
    - domains depends on repositories
    - applications depends on domains
    """
    class _C:
        pass

    c = _C()
    c.repositories = container['repositories']

    if container['infrastructure'] is None:
        container['infrastructure'] = InfrastructureProvider()
    c.infrastructure = container['infrastructure']

    if container['domains'] is None:
        container['domains'] = DomainProvider(repositories=c.repositories)
    c.domains = container['domains']

    if container['applications'] is None:
        container['applications'] = ApplicationProvider(domains=c.domains)
    c.applications = container['applications']

    return c


def reset_container():
    """Reset provider singletons and overrides (useful for tests)."""
    container['repositories'] = RepositoryProvider()
    container['domains'] = None
    container['applications'] = None
    container['infrastructure'] = None
