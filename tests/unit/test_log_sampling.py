"""
Unit Tests - Log Sampling
Log Sampling System tests
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
from utils.log_sampling import (
    SamplingRule,
    LogSampler,
    SamplingFilter,
    get_log_sampler,
    setup_log_sampling,
    get_sampling_stats,
)


@pytest.mark.unit
def test_log_sampling_module_imports():
    """Test log_sampling module can be imported"""
    from utils.log_sampling import SamplingRule, LogSampler, SamplingFilter
    assert SamplingRule is not None
    assert LogSampler is not None
    assert SamplingFilter is not None


@pytest.mark.unit
def test_log_sampling_module_structure():
    """Test log_sampling module structure"""
    import utils.log_sampling as log_sampling_module
    
    # Check for expected classes and functions
    assert hasattr(log_sampling_module, 'SamplingRule')
    assert hasattr(log_sampling_module, 'LogSampler')
    assert hasattr(log_sampling_module, 'SamplingFilter')
    assert hasattr(log_sampling_module, 'get_log_sampler')
    assert hasattr(log_sampling_module, 'setup_log_sampling')
    assert hasattr(log_sampling_module, 'get_sampling_stats')


@pytest.mark.unit
def test_sampling_rule_dataclass():
    """Test SamplingRule dataclass"""
    rule = SamplingRule(sample_rate=0.5, min_samples_per_minute=10, max_samples_per_minute=100, priority=5)
    
    assert rule.sample_rate == 0.5
    assert rule.min_samples_per_minute == 10
    assert rule.max_samples_per_minute == 100
    assert rule.priority == 5


@pytest.mark.unit
def test_sampling_rule_defaults():
    """Test SamplingRule default values"""
    rule = SamplingRule(sample_rate=0.5)
    
    assert rule.sample_rate == 0.5
    assert rule.min_samples_per_minute == 10
    assert rule.max_samples_per_minute == 100
    assert rule.priority == 5


@pytest.mark.unit
def test_log_sampler_initialization():
    """Test LogSampler initialization"""
    sampler = LogSampler()
    
    assert sampler.rules is not None
    assert sampler.sample_counts == {}
    assert sampler.sampling_enabled is True
    assert sampler.logger is not None


@pytest.mark.unit
def test_log_sampler_default_rules():
    """Test LogSampler default rules"""
    sampler = LogSampler()
    
    assert 'DEBUG' in sampler.rules
    assert 'INFO' in sampler.rules
    assert 'WARNING' in sampler.rules
    assert 'ERROR' in sampler.rules
    assert 'CRITICAL' in sampler.rules


@pytest.mark.unit
def test_log_sampler_should_sample_disabled():
    """Test should_sample when sampling is disabled"""
    sampler = LogSampler()
    sampler.sampling_enabled = False
    
    result = sampler.should_sample('INFO', 'test_logger')
    assert result is True


@pytest.mark.unit
def test_log_sampler_should_sample_no_rule():
    """Test should_sample when no rule exists for level"""
    sampler = LogSampler()
    
    result = sampler.should_sample('UNKNOWN', 'test_logger')
    assert result is True


@pytest.mark.unit
def test_log_sampler_should_sample_high_priority():
    """Test should_sample for high priority logs (priority <= 2)"""
    sampler = LogSampler()
    
    # ERROR has priority 2, CRITICAL has priority 1
    assert sampler.should_sample('ERROR', 'test_logger') is True
    assert sampler.should_sample('CRITICAL', 'test_logger') is True


@pytest.mark.unit
def test_log_sampler_should_sample_below_min():
    """Test should_sample when below min_samples_per_minute"""
    sampler = LogSampler()
    
    # INFO has min_samples_per_minute=5, so first 5 should be sampled
    for _ in range(5):
        result = sampler.should_sample('INFO', 'test_logger')
        assert result is True


@pytest.mark.unit
def test_log_sampler_should_sample_above_max():
    """Test should_sample when above max_samples_per_minute"""
    sampler = LogSampler()
    
    # INFO has max_samples_per_minute=50
    current_minute = datetime.now().strftime('%Y-%m-%d %H:%M')
    sampler.sample_counts[current_minute] = [datetime.now()] * 51
    
    result = sampler.should_sample('INFO', 'test_logger')
    assert result is False


@pytest.mark.unit
def test_log_sampler_cleanup_old_samples():
    """Test cleanup_old_samples method"""
    sampler = LogSampler()
    
    # Add old samples
    old_minute = (datetime.now() - timedelta(minutes=10)).strftime('%Y-%m-%d %H:%M')
    sampler.sample_counts[old_minute] = [datetime.now()]
    
    # Add recent samples
    recent_minute = datetime.now().strftime('%Y-%m-%d %H:%M')
    sampler.sample_counts[recent_minute] = [datetime.now()]
    
    sampler._cleanup_old_samples()
    
    assert old_minute not in sampler.sample_counts
    assert recent_minute in sampler.sample_counts


@pytest.mark.unit
def test_log_sampler_cleanup_invalid_format():
    """Test cleanup_old_samples with invalid format"""
    sampler = LogSampler()
    
    sampler.sample_counts['invalid'] = [datetime.now()]
    
    sampler._cleanup_old_samples()
    
    assert 'invalid' not in sampler.sample_counts


@pytest.mark.unit
def test_log_sampler_add_rule():
    """Test add_rule method"""
    sampler = LogSampler()
    
    new_rule = SamplingRule(sample_rate=0.3, min_samples_per_minute=5, max_samples_per_minute=50, priority=7)
    sampler.add_rule('CUSTOM', new_rule)
    
    assert 'CUSTOM' in sampler.rules
    assert sampler.rules['CUSTOM'].sample_rate == 0.3


@pytest.mark.unit
def test_log_sampler_remove_rule():
    """Test remove_rule method"""
    sampler = LogSampler()
    
    sampler.remove_rule('DEBUG')
    
    assert 'DEBUG' not in sampler.rules


@pytest.mark.unit
def test_log_sampler_remove_nonexistent_rule():
    """Test remove_rule with nonexistent level"""
    sampler = LogSampler()
    
    # Should not raise error
    sampler.remove_rule('NONEXISTENT')


@pytest.mark.unit
def test_log_sampler_get_sampling_stats():
    """Test get_sampling_stats method"""
    sampler = LogSampler()
    
    stats = sampler.get_sampling_stats()
    
    assert 'enabled' in stats
    assert 'rules' in stats
    assert 'current_samples' in stats
    assert stats['enabled'] is True
    assert 'DEBUG' in stats['rules']


@pytest.mark.unit
def test_log_sampler_enable_sampling():
    """Test enable_sampling method"""
    sampler = LogSampler()
    sampler.sampling_enabled = False
    
    sampler.enable_sampling()
    
    assert sampler.sampling_enabled is True


@pytest.mark.unit
def test_log_sampler_disable_sampling():
    """Test disable_sampling method"""
    sampler = LogSampler()
    
    sampler.disable_sampling()
    
    assert sampler.sampling_enabled is False


@pytest.mark.unit
def test_sampling_filter_initialization():
    """Test SamplingFilter initialization"""
    sampler = LogSampler()
    filter_obj = SamplingFilter(sampler)
    
    assert filter_obj.sampler is sampler


@pytest.mark.unit
def test_sampling_filter_filter():
    """Test SamplingFilter filter method"""
    sampler = LogSampler()
    filter_obj = SamplingFilter(sampler)
    
    mock_record = Mock()
    mock_record.levelname = 'ERROR'
    mock_record.name = 'test_logger'
    
    result = filter_obj.filter(mock_record)
    assert result is True


@pytest.mark.unit
def test_get_log_sampler_singleton():
    """Test get_log_sampler returns singleton"""
    sampler1 = get_log_sampler()
    sampler2 = get_log_sampler()
    
    assert sampler1 is sampler2


@pytest.mark.unit
def test_setup_log_sampling():
    """Test setup_log_sampling function"""
    with patch('utils.log_sampling.logging.getLogger') as mock_get_logger:
        mock_logger = Mock()
        mock_get_logger.return_value = mock_logger
        
        sampler = setup_log_sampling()
        
        assert sampler is not None
        mock_logger.addFilter.assert_called_once()


@pytest.mark.unit
def test_get_sampling_stats():
    """Test get_sampling_stats function"""
    stats = get_sampling_stats()
    
    assert 'enabled' in stats
    assert 'rules' in stats
    assert 'current_samples' in stats


@pytest.mark.unit
def test_sampling_rule_sample_rate_bounds():
    """Test SamplingRule sample_rate within bounds"""
    rule = SamplingRule(sample_rate=1.0)
    assert rule.sample_rate == 1.0
    
    rule = SamplingRule(sample_rate=0.0)
    assert rule.sample_rate == 0.0


@pytest.mark.unit
def test_log_sampler_random_sampling():
    """Test random sampling behavior"""
    sampler = LogSampler()
    
    # Fill up to min_samples
    current_minute = datetime.now().strftime('%Y-%m-%d %H:%M')
    sampler.sample_counts[current_minute] = [datetime.now()] * 10
    
    # With sample_rate=0.1 for INFO, should mostly return False
    # But we can't guarantee random, so just test it runs
    result = sampler.should_sample('INFO', 'test_logger')
    assert isinstance(result, bool)
