"""
Unit Tests — Financial Engine Caching & Resilience (Faz 4)
Tests in-memory TTL caching, granular tenant invalidation, and write-through cache eviction.
"""
from unittest.mock import MagicMock, patch

import pytest

from engines.financial_engine import (
    ASSET_ANALYSIS_CACHE,
    FINANCIAL_ANALYSIS_CACHE,
    FREEDOM_ANALYSIS_CACHE,
    MONTHLY_DASHBOARD_CACHE,
    get_asset_analysis,
    get_financial_freedom_analysis,
    invalidate_financial_cache,
)
from models import Transaction
from repositories.transaction_repository import TransactionRepository


@pytest.fixture(autouse=True)
def clean_engine_caches():
    """Ensure caches are reset before and after every test."""
    invalidate_financial_cache(None)
    yield
    invalidate_financial_cache(None)


@pytest.mark.unit
def test_invalidate_financial_cache_all_tenants():
    # Populate caches with dummy data
    FINANCIAL_ANALYSIS_CACHE["data"]["tenant_1"] = {"val": 1}
    FINANCIAL_ANALYSIS_CACHE["last_fetched"]["tenant_1"] = 123.0
    MONTHLY_DASHBOARD_CACHE["data"]["tenant_1_2026"] = {"val": 2}
    MONTHLY_DASHBOARD_CACHE["last_fetched"]["tenant_1_2026"] = 123.0
    ASSET_ANALYSIS_CACHE["data"]["tenant_2"] = {"val": 3}
    ASSET_ANALYSIS_CACHE["last_fetched"]["tenant_2"] = 123.0
    FREEDOM_ANALYSIS_CACHE["data"]["tenant_2_default"] = {"val": 4}
    FREEDOM_ANALYSIS_CACHE["last_fetched"]["tenant_2_default"] = 123.0

    invalidate_financial_cache(None)

    assert len(FINANCIAL_ANALYSIS_CACHE["data"]) == 0
    assert len(MONTHLY_DASHBOARD_CACHE["data"]) == 0
    assert len(ASSET_ANALYSIS_CACHE["data"]) == 0
    assert len(FREEDOM_ANALYSIS_CACHE["data"]) == 0


@pytest.mark.unit
def test_invalidate_financial_cache_specific_tenant():
    # Setup data for two tenants
    FINANCIAL_ANALYSIS_CACHE["data"]["tenant_1"] = {"val": 1}
    FINANCIAL_ANALYSIS_CACHE["last_fetched"]["tenant_1"] = 123.0
    MONTHLY_DASHBOARD_CACHE["data"]["tenant_1_2026"] = {"val": 2}
    MONTHLY_DASHBOARD_CACHE["last_fetched"]["tenant_1_2026"] = 123.0

    FINANCIAL_ANALYSIS_CACHE["data"]["tenant_2"] = {"val": 10}
    FINANCIAL_ANALYSIS_CACHE["last_fetched"]["tenant_2"] = 123.0
    MONTHLY_DASHBOARD_CACHE["data"]["tenant_2_2026"] = {"val": 20}
    MONTHLY_DASHBOARD_CACHE["last_fetched"]["tenant_2_2026"] = 123.0

    # Invalidate only tenant_1
    invalidate_financial_cache("tenant_1")

    assert "tenant_1" not in FINANCIAL_ANALYSIS_CACHE["data"]
    assert "tenant_1_2026" not in MONTHLY_DASHBOARD_CACHE["data"]
    # tenant_2 must remain untouched
    assert "tenant_2" in FINANCIAL_ANALYSIS_CACHE["data"]
    assert "tenant_2_2026" in MONTHLY_DASHBOARD_CACHE["data"]


@pytest.mark.unit
def test_get_asset_analysis_caching(app):
    with app.app_context():
        tenant_id = "test_asset_tenant"
        # First call: populates cache
        res1 = get_asset_analysis(tenant_id)
        assert tenant_id in ASSET_ANALYSIS_CACHE["data"]
        assert ASSET_ANALYSIS_CACHE["data"][tenant_id] == res1

        # Modify cached object in-place to verify second call serves from cache
        ASSET_ANALYSIS_CACHE["data"][tenant_id]["cached_marker"] = True
        res2 = get_asset_analysis(tenant_id)
        assert res2.get("cached_marker") is True

        # Invalidate cache
        invalidate_financial_cache(tenant_id)
        assert tenant_id not in ASSET_ANALYSIS_CACHE["data"]

        # Call again: freshly calculated, marker gone
        res3 = get_asset_analysis(tenant_id)
        assert "cached_marker" not in res3


@pytest.mark.unit
def test_get_financial_freedom_analysis_caching(app):
    with app.app_context():
        tenant_id = "test_freedom_tenant"
        _ = get_financial_freedom_analysis(tenant_id)
        cache_key = f"{tenant_id}_default"
        assert cache_key in FREEDOM_ANALYSIS_CACHE["data"]

        # Mark cache
        FREEDOM_ANALYSIS_CACHE["data"][cache_key]["marker"] = "hit"
        res2 = get_financial_freedom_analysis(tenant_id)
        assert res2.get("marker") == "hit"

        # Invalidate
        invalidate_financial_cache(tenant_id)
        assert cache_key not in FREEDOM_ANALYSIS_CACHE["data"]


@pytest.mark.unit
def test_transaction_repository_write_invalidates_cache(app):
    with app.app_context():
        repo = TransactionRepository()
        tenant_id = "tx_cache_test_tenant"
        FINANCIAL_ANALYSIS_CACHE["data"][tenant_id] = {"stale": True}

        # Mock commit and db operations
        with patch.object(repo, 'commit', return_value=None), \
             patch('repositories.transaction_repository.invalidate_financial_cache') as mock_inv:
            # We call delete_transaction on a mock transaction
            mock_tx = MagicMock(id=1, tenant_id=tenant_id, status='Bekliyor')
            with patch('repositories.transaction_repository.Transaction.query') as mock_query:
                mock_query.filter_by.return_value.first.return_value = mock_tx
                with patch.object(repo.session, 'delete', return_value=None):
                    repo.delete_transaction(1, tenant_id=tenant_id)

            mock_inv.assert_called_with(tenant_id)


@pytest.mark.unit
def test_transaction_origin_request_scoped_caching(app):
    with app.test_request_context():
        tx = Transaction()
        tx.source_type = 'asset'
        tx.source_id = 999
        tx.tenant_id = 't1'

        with patch('models.db.session.get') as mock_get:
            mock_asset = MagicMock()
            mock_asset.tenant_id = 't1'
            mock_asset.type = 'Hisse'
            mock_get.return_value = mock_asset

            # First access
            origin1 = tx.origin
            assert origin1 == 'Hisse Alımı'
            assert mock_get.call_count == 1

            # Second access within same request
            origin2 = tx.origin
            assert origin2 == 'Hisse Alımı'
            # Should have hit g._asset_type_cache, NOT db.session.get again
            assert mock_get.call_count == 1
