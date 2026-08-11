"""
Unit Tests - Portfolio Repository
Repository for portfolio asset persistence operations
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from repositories.portfolio_repository import PortfolioRepository


@pytest.mark.unit
def test_portfolio_repository_init():
    """Test PortfolioRepository initialization"""
    mock_db = Mock()
    mock_session = Mock()
    mock_db.session = mock_session
    
    repo = PortfolioRepository(database=mock_db)
    
    assert repo.session == mock_session


@pytest.mark.unit
def test_portfolio_repository_imports():
    """Test that PortfolioRepository can be imported"""
    from repositories.portfolio_repository import PortfolioRepository
    
    assert PortfolioRepository is not None


@pytest.mark.unit
def test_portfolio_repository_module_structure():
    """Test portfolio_repository module structure"""
    import repositories.portfolio_repository as portfolio_repo_module
    
    # Check for expected class
    assert hasattr(portfolio_repo_module, 'PortfolioRepository')
    
    # Check for expected imports
    assert hasattr(portfolio_repo_module, 'Asset')
    assert hasattr(portfolio_repo_module, 'AssetUpdate')
    assert hasattr(portfolio_repo_module, 'BaseRepository')


@pytest.mark.unit
def test_portfolio_repository_extends_base():
    """Test PortfolioRepository extends BaseRepository"""
    from repositories.portfolio_repository import PortfolioRepository
    from repositories.base import BaseRepository
    
    assert issubclass(PortfolioRepository, BaseRepository)


@pytest.mark.unit
def test_add_asset():
    """Test add_asset method"""
    mock_db = Mock()
    mock_session = Mock()
    mock_db.session = mock_session
    
    with patch('repositories.portfolio_repository.Asset') as mock_asset_class:
        mock_asset = Mock()
        mock_asset_class.return_value = mock_asset
        
        repo = PortfolioRepository(database=mock_db)
        repo.commit = Mock()
        
        result = repo.add_asset(
            type_='stock',
            name='Test Asset',
            value=1000.0,
            description='Test description',
            tenant_id='test_tenant'
        )
        
        assert result == mock_asset
        mock_session.add.assert_called_once_with(mock_asset)
        repo.commit.assert_called_once()


@pytest.mark.unit
def test_add_asset_with_all_parameters():
    """Test add_asset with all parameters"""
    mock_db = Mock()
    mock_session = Mock()
    mock_db.session = mock_session
    
    with patch('repositories.portfolio_repository.Asset') as mock_asset_class:
        mock_asset = Mock()
        mock_asset_class.return_value = mock_asset
        
        repo = PortfolioRepository(database=mock_db)
        repo.commit = Mock()
        
        result = repo.add_asset(
            type_='stock',
            name='Test Asset',
            value=1000.0,
            description='Test description',
            purchase_date='2024-01-01',
            purchase_cost=900.0,
            quantity=10.0,
            unit_price=100.0,
            currency='USD',
            symbol='AAPL',
            risk_level='Yüksek',
            liquidity='Likit',
            sector_id=1,
            notes='Test notes',
            tenant_id='test_tenant'
        )
        
        assert result == mock_asset
        mock_session.add.assert_called_once_with(mock_asset)


@pytest.mark.unit
def test_update_asset():
    """Test update_asset method"""
    mock_db = Mock()
    mock_session = Mock()
    mock_db.session = mock_session
    mock_asset = Mock()
    mock_db.get_or_404.return_value = mock_asset
    
    repo = PortfolioRepository(database=mock_db)
    repo.commit = Mock()
    
    result = repo.update_asset(
        asset_id=1,
        type_='stock',
        name='Updated Asset',
        value=2000.0,
        description='Updated description'
    )
    
    assert result == mock_asset
    mock_db.get_or_404.assert_called_once()
    repo.commit.assert_called_once()


@pytest.mark.unit
def test_delete_asset():
    """Test delete_asset method"""
    mock_db = Mock()
    mock_session = Mock()
    mock_db.session = mock_session
    
    with patch('domain.transactions.services.financial_ledger.delete_asset_position') as mock_delete:
        mock_delete.return_value = True
        
        repo = PortfolioRepository(database=mock_db)
        result = repo.delete_asset(asset_id=1)
        
        assert result == True
        mock_delete.assert_called_once_with(1)


@pytest.mark.unit
def test_log_asset_update():
    """Test log_asset_update method"""
    mock_db = Mock()
    mock_session = Mock()
    mock_db.session = mock_session
    
    with patch('repositories.portfolio_repository.AssetUpdate') as mock_update_class:
        mock_update = Mock()
        mock_update_class.return_value = mock_update
        
        repo = PortfolioRepository(database=mock_db)
        repo.commit = Mock()
        
        result = repo.log_asset_update(
            asset_id=1,
            old_value=1000.0,
            new_value=2000.0,
            user_id=1
        )
        
        assert result == mock_update
        mock_session.add.assert_called_once_with(mock_update)
        repo.commit.assert_called_once()


@pytest.mark.unit
def test_log_asset_update_no_auto_commit():
    """Test log_asset_update with auto_commit=False"""
    mock_db = Mock()
    mock_session = Mock()
    mock_db.session = mock_session
    
    with patch('repositories.portfolio_repository.AssetUpdate') as mock_update_class:
        mock_update = Mock()
        mock_update_class.return_value = mock_update
        
        repo = PortfolioRepository(database=mock_db)
        repo.commit = Mock()
        
        result = repo.log_asset_update(
            asset_id=1,
            old_value=1000.0,
            new_value=2000.0,
            auto_commit=False
        )
        
        assert result == mock_update
        mock_session.add.assert_called_once_with(mock_update)
        repo.commit.assert_not_called()


@pytest.mark.unit
def test_get_asset_update_history():
    """Test get_asset_update_history method"""
    mock_db = Mock()
    mock_session = Mock()
    mock_db.session = mock_session
    mock_query = Mock()
    mock_updates = [Mock(), Mock()]
    
    with patch('repositories.portfolio_repository.AssetUpdate') as mock_update_class:
        repo = PortfolioRepository(database=mock_db)
        repo.query = Mock(return_value=mock_query)
        mock_query.filter_by.return_value.order_by.return_value.limit.return_value.all.return_value = mock_updates
        
        result = repo.get_asset_update_history(asset_id=1, limit=50)
        
        assert result == mock_updates


@pytest.mark.unit
def test_bulk_update_assets():
    """Test bulk_update_assets method"""
    mock_db = Mock()
    mock_session = Mock()
    mock_db.session = mock_session
    mock_asset = Mock()
    mock_asset.id = 1
    mock_asset.quantity = 10
    mock_asset.value = 1000
    mock_asset.unit_price = 100
    mock_db.session.get.return_value = mock_asset
    
    with patch('repositories.portfolio_repository.AssetUpdate') as mock_update_class:
        mock_update = Mock()
        mock_update_class.return_value = mock_update
        
        repo = PortfolioRepository(database=mock_db)
        result = repo.bulk_update_assets(
            asset_ids=[1],
            new_unit_prices=[150.0],
            user_id=1,
            notes='Bulk update'
        )
        
        assert len(result) == 1
        mock_db.session.commit.assert_called_once()


@pytest.mark.unit
def test_portfolio_repository_module_has_required_imports():
    """Test portfolio_repository module has required imports"""
    import repositories.portfolio_repository as portfolio_repo_module
    
    # Custom imports
    assert hasattr(portfolio_repo_module, 'Asset')
    assert hasattr(portfolio_repo_module, 'AssetUpdate')
    assert hasattr(portfolio_repo_module, 'BaseRepository')
    assert hasattr(portfolio_repo_module, 'BaseRepositoryContract')
    assert hasattr(portfolio_repo_module, 'PortfolioRepositoryContract')


@pytest.mark.unit
def test_add_asset_default_parameters():
    """Test add_asset with default parameters"""
    mock_db = Mock()
    mock_session = Mock()
    mock_db.session = mock_session
    
    with patch('repositories.portfolio_repository.Asset') as mock_asset_class:
        mock_asset = Mock()
        mock_asset_class.return_value = mock_asset
        
        repo = PortfolioRepository(database=mock_db)
        repo.commit = Mock()
        
        result = repo.add_asset(
            type_='stock',
            name='Test Asset',
            value=1000.0,
            description='Test description'
        )
        
        assert result == mock_asset
        mock_session.add.assert_called_once_with(mock_asset)


@pytest.mark.unit
def test_update_asset_with_all_parameters():
    """Test update_asset with all parameters"""
    mock_db = Mock()
    mock_session = Mock()
    mock_db.session = mock_session
    mock_asset = Mock()
    mock_db.get_or_404.return_value = mock_asset
    
    repo = PortfolioRepository(database=mock_db)
    repo.commit = Mock()
    
    result = repo.update_asset(
        asset_id=1,
        type_='stock',
        name='Updated Asset',
        value=2000.0,
        description='Updated description',
        purchase_date='2024-01-01',
        purchase_cost=900.0,
        quantity=10.0,
        unit_price=200.0,
        currency='USD',
        symbol='AAPL',
        risk_level='Yüksek',
        liquidity='Likit',
        sector_id=1,
        notes='Updated notes'
    )
    
    assert result == mock_asset
    assert mock_asset.type == 'stock'
    assert mock_asset.name == 'Updated Asset'
    assert mock_asset.value == 2000.0


@pytest.mark.unit
def test_log_asset_update_with_unit_prices():
    """Test log_asset_update with unit prices"""
    mock_db = Mock()
    mock_session = Mock()
    mock_db.session = mock_session
    
    with patch('repositories.portfolio_repository.AssetUpdate') as mock_update_class:
        mock_update = Mock()
        mock_update_class.return_value = mock_update
        
        repo = PortfolioRepository(database=mock_db)
        repo.commit = Mock()
        
        result = repo.log_asset_update(
            asset_id=1,
            old_value=1000.0,
            new_value=2000.0,
            old_unit_price=100.0,
            new_unit_price=200.0,
            update_type='market',
            update_source='api',
            notes='Market update',
            user_id=1
        )
        
        assert result == mock_update
        mock_session.add.assert_called_once_with(mock_update)


@pytest.mark.unit
def test_get_asset_update_history_custom_limit():
    """Test get_asset_update_history with custom limit"""
    mock_db = Mock()
    mock_session = Mock()
    mock_db.session = mock_session
    mock_query = Mock()
    mock_updates = [Mock()]
    
    with patch('repositories.portfolio_repository.AssetUpdate') as mock_update_class:
        repo = PortfolioRepository(database=mock_db)
        repo.query = Mock(return_value=mock_query)
        mock_query.filter_by.return_value.order_by.return_value.limit.return_value.all.return_value = mock_updates
        
        result = repo.get_asset_update_history(asset_id=1, limit=10)
        
        assert result == mock_updates


@pytest.mark.unit
def test_bulk_update_assets_multiple_assets():
    """Test bulk_update_assets with multiple assets"""
    mock_db = Mock()
    mock_session = Mock()
    mock_db.session = mock_session
    mock_asset1 = Mock()
    mock_asset1.id = 1
    mock_asset1.quantity = 10
    mock_asset1.value = 1000
    mock_asset1.unit_price = 100
    mock_asset2 = Mock()
    mock_asset2.id = 2
    mock_asset2.quantity = 5
    mock_asset2.value = 500
    mock_asset2.unit_price = 100
    
    mock_db.session.get.side_effect = [mock_asset1, mock_asset2]
    
    with patch('repositories.portfolio_repository.AssetUpdate') as mock_update_class:
        mock_update = Mock()
        mock_update_class.return_value = mock_update
        
        repo = PortfolioRepository(database=mock_db)
        result = repo.bulk_update_assets(
            asset_ids=[1, 2],
            new_unit_prices=[150.0, 120.0],
            user_id=1
        )
        
        assert len(result) == 2
        mock_db.session.commit.assert_called_once()


@pytest.mark.unit
def test_bulk_update_assets_asset_not_found():
    """Test bulk_update_assets when asset not found"""
    mock_db = Mock()
    mock_session = Mock()
    mock_db.session = mock_session
    mock_db.session.get.return_value = None
    
    with patch('repositories.portfolio_repository.AssetUpdate') as mock_update_class:
        mock_update = Mock()
        mock_update_class.return_value = mock_update
        
        repo = PortfolioRepository(database=mock_db)
        result = repo.bulk_update_assets(
            asset_ids=[1],
            new_unit_prices=[150.0],
            user_id=1
        )
        
        assert len(result) == 0
        mock_db.session.commit.assert_called_once()
