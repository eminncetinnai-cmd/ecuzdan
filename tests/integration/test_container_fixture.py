"""Tests for Composition Root container fixture and override behavior."""


def test_container_repository_override(container):
    """Test that repository overrides propagate through the provider chain."""
    class FakeFinancialRepository:
        pass

    fake = FakeFinancialRepository()
    # override the financial repository before creating applications
    container.repositories.set_override('financial', fake)

    # obtain the application provider and portfolio application
    portfolio_app = container.applications.portfolio()

    # The portfolio application's asset_service should have the fake injected
    assert getattr(portfolio_app.asset_service, 'financial_repository') is fake


def test_container_domain_override(container):
    """Test that domain service overrides work correctly."""
    class FakeCatalogService:
        def __init__(self):
            self.repository = None

    fake = FakeCatalogService()
    # override the catalog domain service
    container.domains.set_override('catalog', fake)

    # obtain the application provider and catalog application
    catalog_app = container.applications.catalog()

    # The catalog application should have the fake service injected
    assert catalog_app._svc is fake
