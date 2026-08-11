"""
Unit Tests - Log Retention
Log retention policy and cleanup utilities
"""

import pytest
import os
import tempfile
import shutil
from unittest.mock import Mock, patch, MagicMock
from utils.log_retention import (
    LogRetentionConfig,
    LogRetentionManager,
    get_log_retention_manager,
    setup_log_retention,
)


@pytest.mark.unit
def test_log_retention_config_defaults():
    """Test LogRetentionConfig default values"""
    config = LogRetentionConfig()
    assert config.detailed_logs_retention_days == 30
    assert config.error_logs_retention_days == 90
    assert config.security_logs_retention_days == 365
    assert config.max_log_size_mb == 100
    assert config.max_total_log_size_mb == 500
    assert config.enable_compression is True
    assert config.archive_dir == 'logs/archive'
    assert config.auto_cleanup_enabled is True


@pytest.mark.unit
def test_log_retention_manager_initialization():
    """Test LogRetentionManager initialization"""
    manager = LogRetentionManager()
    assert manager.config is not None
    assert manager.logger is not None
    assert manager.log_dir is not None


@pytest.mark.unit
def test_log_retention_manager_custom_config():
    """Test LogRetentionManager with custom config"""
    config = LogRetentionConfig()
    config.detailed_logs_retention_days = 60
    manager = LogRetentionManager(config)
    assert manager.config.detailed_logs_retention_days == 60


@pytest.mark.unit
def test_cleanup_old_logs_disabled():
    """Test cleanup_old_logs when auto_cleanup is disabled"""
    config = LogRetentionConfig()
    config.auto_cleanup_enabled = False
    manager = LogRetentionManager(config)
    
    # Should not raise exception
    manager.cleanup_old_logs()


@pytest.mark.unit
def test_get_retention_days():
    """Test _get_retention_days method"""
    manager = LogRetentionManager()
    assert manager._get_retention_days('detailed') == 30
    assert manager._get_retention_days('error') == 90
    assert manager._get_retention_days('security') == 365
    assert manager._get_retention_days('unknown') == 30


@pytest.mark.unit
def test_get_log_stats_empty_directory():
    """Test get_log_stats with empty directory"""
    with tempfile.TemporaryDirectory() as temp_dir:
        manager = LogRetentionManager()
        manager.log_dir = temp_dir
        
        stats = manager.get_log_stats()
        assert stats['total_files'] == 0
        assert stats['total_size_mb'] == 0
        assert stats['files_by_type']['detailed']['count'] == 0
        assert stats['files_by_type']['error']['count'] == 0
        assert stats['files_by_type']['security']['count'] == 0
        assert stats['files_by_type']['archive']['count'] == 0


@pytest.mark.unit
def test_get_log_retention_manager_singleton():
    """Test get_log_retention_manager returns singleton"""
    manager1 = get_log_retention_manager()
    manager2 = get_log_retention_manager()
    assert manager1 is manager2


@pytest.mark.unit
def test_setup_log_retention():
    """Test setup_log_retention with custom config"""
    config = LogRetentionConfig()
    config.detailed_logs_retention_days = 45
    
    manager = setup_log_retention(config)
    assert manager.config.detailed_logs_retention_days == 45


@pytest.mark.unit
def test_log_retention_config_attributes():
    """Test LogRetentionConfig has all required attributes"""
    config = LogRetentionConfig()
    assert hasattr(config, 'detailed_logs_retention_days')
    assert hasattr(config, 'error_logs_retention_days')
    assert hasattr(config, 'security_logs_retention_days')
    assert hasattr(config, 'max_log_size_mb')
    assert hasattr(config, 'max_total_log_size_mb')
    assert hasattr(config, 'enable_compression')
    assert hasattr(config, 'archive_dir')
    assert hasattr(config, 'auto_cleanup_enabled')


@pytest.mark.unit
def test_log_retention_manager_methods():
    """Test LogRetentionManager has all required methods"""
    manager = LogRetentionManager()
    assert hasattr(manager, 'cleanup_old_logs')
    assert hasattr(manager, '_get_log_files')
    assert hasattr(manager, '_get_file_age_days')
    assert hasattr(manager, '_get_retention_days')
    assert hasattr(manager, '_archive_or_delete')
    assert hasattr(manager, '_compress_and_archive')
    assert hasattr(manager, 'check_disk_space')
    assert hasattr(manager, 'get_log_stats')


@pytest.mark.unit
def test_log_retention_imports():
    """Test that all log retention functions can be imported"""
    from utils.log_retention import (
        LogRetentionConfig,
        LogRetentionManager,
        get_log_retention_manager,
        setup_log_retention,
    )
    
    assert LogRetentionConfig is not None
    assert LogRetentionManager is not None
    assert callable(get_log_retention_manager)
    assert callable(setup_log_retention)


@pytest.mark.unit
def test_log_retention_config_custom_values():
    """Test LogRetentionConfig with custom values"""
    config = LogRetentionConfig()
    config.detailed_logs_retention_days = 15
    config.error_logs_retention_days = 45
    config.security_logs_retention_days = 180
    config.max_log_size_mb = 50
    config.max_total_log_size_mb = 250
    config.enable_compression = False
    config.archive_dir = 'custom/archive'
    config.auto_cleanup_enabled = False
    
    assert config.detailed_logs_retention_days == 15
    assert config.error_logs_retention_days == 45
    assert config.security_logs_retention_days == 180
    assert config.max_log_size_mb == 50
    assert config.max_total_log_size_mb == 250
    assert config.enable_compression is False
    assert config.archive_dir == 'custom/archive'
    assert config.auto_cleanup_enabled is False


@pytest.mark.unit
def test_get_log_files_method_exists():
    """Test _get_log_files method exists and returns list"""
    manager = LogRetentionManager()
    result = manager._get_log_files()
    assert isinstance(result, list)


@pytest.mark.unit
def test_get_file_age_days_method_exists():
    """Test _get_file_age_days method exists"""
    manager = LogRetentionManager()
    assert callable(manager._get_file_age_days)


@pytest.mark.unit
def test_archive_or_delete_method_exists():
    """Test _archive_or_delete method exists"""
    manager = LogRetentionManager()
    assert callable(manager._archive_or_delete)


@pytest.mark.unit
def test_compress_and_archive_method_exists():
    """Test _compress_and_archive method exists"""
    manager = LogRetentionManager()
    assert callable(manager._compress_and_archive)


@pytest.mark.unit
def test_check_disk_space_method_exists():
    """Test check_disk_space method exists"""
    manager = LogRetentionManager()
    assert callable(manager.check_disk_space)


@pytest.mark.unit
def test_get_log_stats_method_exists():
    """Test get_log_stats method exists"""
    manager = LogRetentionManager()
    assert callable(manager.get_log_stats)


@pytest.mark.unit
def test_log_retention_manager_logger():
    """Test LogRetentionManager has logger"""
    manager = LogRetentionManager()
    assert manager.logger is not None
    assert hasattr(manager.logger, 'info')
    assert hasattr(manager.logger, 'error')
    assert hasattr(manager.logger, 'warning')


@pytest.mark.unit
def test_cleanup_old_logs_with_files():
    """Test cleanup_old_logs with log files"""
    with tempfile.TemporaryDirectory() as temp_dir:
        manager = LogRetentionManager()
        manager.log_dir = temp_dir
        
        # Create a test log file
        test_file = os.path.join(temp_dir, 'e_cuzdan.log')
        with open(test_file, 'w') as f:
            f.write('test log content')
        
        # Mock _get_file_age_days to return old age
        with patch.object(manager, '_get_file_age_days', return_value=100):
            with patch.object(manager, '_archive_or_delete') as mock_archive:
                manager.cleanup_old_logs()
                mock_archive.assert_called()


@pytest.mark.unit
def test_cleanup_old_logs_exception_handling():
    """Test cleanup_old_logs exception handling"""
    manager = LogRetentionManager()
    
    with patch.object(manager, '_get_log_files', side_effect=Exception("Test error")):
        # Should not raise exception
        manager.cleanup_old_logs()


@pytest.mark.unit
def test_get_log_files_with_rotation_files():
    """Test _get_log_files with rotation files"""
    with tempfile.TemporaryDirectory() as temp_dir:
        manager = LogRetentionManager()
        manager.log_dir = temp_dir
        
        # Create rotation files
        for ext in ['.1', '.2', '.gz']:
            test_file = os.path.join(temp_dir, f'e_cuzdan{ext}')
            with open(test_file, 'w') as f:
                f.write('test')
        
        log_files = manager._get_log_files()
        assert len(log_files) == 3


@pytest.mark.unit
def test_get_file_age_days():
    """Test _get_file_age_days method"""
    with tempfile.TemporaryDirectory() as temp_dir:
        manager = LogRetentionManager()
        
        test_file = os.path.join(temp_dir, 'test.log')
        with open(test_file, 'w') as f:
            f.write('test')
        
        age = manager._get_file_age_days(test_file)
        assert age >= 0


@pytest.mark.unit
def test_archive_or_delete_with_compression():
    """Test _archive_or_delete with compression enabled"""
    with tempfile.TemporaryDirectory() as temp_dir:
        config = LogRetentionConfig()
        config.enable_compression = True
        manager = LogRetentionManager(config)
        manager.log_dir = temp_dir
        
        test_file = os.path.join(temp_dir, 'test.log')
        with open(test_file, 'w') as f:
            f.write('test content')
        
        with patch.object(manager, '_compress_and_archive') as mock_compress:
            manager._archive_or_delete(test_file, 10)
            mock_compress.assert_called()


@pytest.mark.unit
def test_archive_or_delete_without_compression():
    """Test _archive_or_delete without compression"""
    with tempfile.TemporaryDirectory() as temp_dir:
        config = LogRetentionConfig()
        config.enable_compression = False
        manager = LogRetentionManager(config)
        manager.log_dir = temp_dir
        
        test_file = os.path.join(temp_dir, 'test.log')
        with open(test_file, 'w') as f:
            f.write('test content')
        
        manager._archive_or_delete(test_file, 5)
        assert not os.path.exists(test_file)


@pytest.mark.unit
def test_compress_and_archive():
    """Test _compress_and_archive method"""
    with tempfile.TemporaryDirectory() as temp_dir:
        manager = LogRetentionManager()
        manager.log_dir = temp_dir
        
        test_file = os.path.join(temp_dir, 'test.log')
        with open(test_file, 'w') as f:
            f.write('test content')
        
        manager._compress_and_archive(test_file)
        
        # Check archive directory was created
        archive_dir = os.path.join(temp_dir, manager.config.archive_dir)
        assert os.path.exists(archive_dir)
        
        # Check original file was deleted
        assert not os.path.exists(test_file)


@pytest.mark.unit
def test_compress_and_archive_exception_handling():
    """Test _compress_and_archive exception handling"""
    manager = LogRetentionManager()
    
    with patch('os.makedirs', side_effect=Exception("Test error")):
        # Should not raise exception
        manager._compress_and_archive('/nonexistent/file.log')


@pytest.mark.unit
def test_check_disk_space_within_limit():
    """Test check_disk_space when within limit"""
    with tempfile.TemporaryDirectory() as temp_dir:
        manager = LogRetentionManager()
        manager.log_dir = temp_dir
        
        # Create a small file
        test_file = os.path.join(temp_dir, 'test.log')
        with open(test_file, 'w') as f:
            f.write('test')
        
        with patch.object(manager, 'cleanup_old_logs') as mock_cleanup:
            manager.check_disk_space()
            mock_cleanup.assert_not_called()


@pytest.mark.unit
def test_check_disk_space_exceeds_limit():
    """Test check_disk_space when limit exceeded"""
    with tempfile.TemporaryDirectory() as temp_dir:
        config = LogRetentionConfig()
        config.max_total_log_size_mb = 0.001  # Very small limit
        manager = LogRetentionManager(config)
        manager.log_dir = temp_dir
        
        # Create a file with enough content to exceed limit
        test_file = os.path.join(temp_dir, 'test.log')
        with open(test_file, 'w') as f:
            f.write('test' * 10000)  # Create larger file
        
        with patch.object(manager, 'cleanup_old_logs') as mock_cleanup:
            manager.check_disk_space()
            mock_cleanup.assert_called()


@pytest.mark.unit
def test_check_disk_space_exception_handling():
    """Test check_disk_space exception handling"""
    manager = LogRetentionManager()
    
    with patch('os.listdir', side_effect=Exception("Test error")):
        # Should not raise exception
        manager.check_disk_space()


@pytest.mark.unit
def test_get_log_stats_with_files():
    """Test get_log_stats with log files"""
    with tempfile.TemporaryDirectory() as temp_dir:
        manager = LogRetentionManager()
        manager.log_dir = temp_dir
        
        # Create test files
        with open(os.path.join(temp_dir, 'e_cuzdan.log'), 'w') as f:
            f.write('test')
        with open(os.path.join(temp_dir, 'e_cuzdan_errors.log'), 'w') as f:
            f.write('test')
        with open(os.path.join(temp_dir, 'e_cuzdan_security.log'), 'w') as f:
            f.write('test')
        
        stats = manager.get_log_stats()
        assert stats['total_files'] == 3
        assert stats['files_by_type']['detailed']['count'] == 1
        assert stats['files_by_type']['error']['count'] == 1
        assert stats['files_by_type']['security']['count'] == 1


@pytest.mark.unit
def test_get_log_stats_with_archive_files():
    """Test get_log_stats with archive files"""
    with tempfile.TemporaryDirectory() as temp_dir:
        manager = LogRetentionManager()
        manager.log_dir = temp_dir
        
        # Create archive file
        with open(os.path.join(temp_dir, 'archive.log.gz'), 'w') as f:
            f.write('test')
        
        stats = manager.get_log_stats()
        assert stats['files_by_type']['archive']['count'] == 1


@pytest.mark.unit
def test_get_log_stats_exception_handling():
    """Test get_log_stats exception handling"""
    manager = LogRetentionManager()
    
    with patch('os.listdir', side_effect=Exception("Test error")):
        stats = manager.get_log_stats()
        assert stats == {}
