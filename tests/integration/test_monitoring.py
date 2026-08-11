"""
Integration Tests - Monitoring API
Monitoring endpoints ve dashboard entegrasyon testleri
"""

import pytest
import json
from unittest.mock import Mock, patch


@pytest.mark.integration
def test_monitoring_dashboard_route(authenticated_client):
    """Monitoring dashboard route testi"""
    response = authenticated_client.get('/monitoring', follow_redirects=True)
    assert response.status_code == 200
    assert b'monitoring' in response.data.lower()


@pytest.mark.integration
def test_monitoring_stats_api(authenticated_client):
    """Monitoring stats API testi"""
    response = authenticated_client.get('/monitoring/api/stats')
    assert response.status_code == 200
    
    data = json.loads(response.data)
    assert 'success' in data
    assert 'data' in data
    assert data['success'] is True


@pytest.mark.integration
def test_monitoring_stats_structure(authenticated_client):
    """Monitoring stats yapısı testi"""
    response = authenticated_client.get('/monitoring/api/stats')
    data = json.loads(response.data)
    
    stats = data['data']
    required_fields = [
        'total_logs', 'error_count', 'warning_count', 
        'critical_count', 'security_count', 'log_files'
    ]
    
    for field in required_fields:
        assert field in stats


@pytest.mark.integration
def test_monitoring_health_api(authenticated_client):
    """Monitoring health API testi"""
    response = authenticated_client.get('/monitoring/api/health')
    assert response.status_code == 200
    
    data = json.loads(response.data)
    assert 'success' in data
    assert 'data' in data
    assert data['success'] is True


@pytest.mark.integration
def test_monitoring_health_structure(authenticated_client):
    """Monitoring health yapısı testi"""
    response = authenticated_client.get('/monitoring/api/health')
    data = json.loads(response.data)
    
    health = data['data']
    required_fields = ['status', 'components', 'disk_usage', 'issues']
    
    for field in required_fields:
        assert field in health


@pytest.mark.integration
def test_monitoring_logs_api(authenticated_client):
    """Monitoring logs API testi"""
    response = authenticated_client.get('/monitoring/api/logs?file=e_cuzdan&lines=10')
    assert response.status_code == 200
    
    data = json.loads(response.data)
    assert 'success' in data
    assert 'data' in data
    assert data['success'] is True


@pytest.mark.integration
def test_monitoring_logs_with_filter(authenticated_client):
    """Monitoring logs filtreleme testi"""
    response = authenticated_client.get('/monitoring/api/logs?file=e_cuzdan&lines=10&level=ERROR')
    assert response.status_code == 200
    
    data = json.loads(response.data)
    assert 'success' in data
    assert 'data' in data
    assert data['success'] is True


@pytest.mark.integration
def test_monitoring_logs_with_search(authenticated_client):
    """Monitoring logs arama testi"""
    response = authenticated_client.get('/monitoring/api/logs?file=e_cuzdan&lines=10&search=test')
    assert response.status_code == 200
    
    data = json.loads(response.data)
    assert 'success' in data
    assert 'data' in data
    assert data['success'] is True


@pytest.mark.integration
def test_monitoring_alerts_config_api(authenticated_client):
    """Monitoring alerts config API testi"""
    response = authenticated_client.get('/monitoring/api/alerts/config')
    assert response.status_code == 200
    
    data = json.loads(response.data)
    assert 'success' in data
    assert 'data' in data
    assert data['success'] is True


@pytest.mark.integration
def test_monitoring_requires_auth(client):
    """Monitoring endpoint auth gerektirir"""
    response = client.get('/monitoring')
    # Should redirect to login or return 401/403
    assert response.status_code in [302, 308, 401, 403]


@pytest.mark.integration
def test_monitoring_api_requires_auth(client):
    """Monitoring API auth gerektirir"""
    response = client.get('/monitoring/api/stats')
    # Should return 401, 403, or redirect to login (302)
    assert response.status_code in [401, 403, 302]


@pytest.mark.integration
def test_monitoring_dashboard_components(authenticated_client):
    """Monitoring dashboard bileşenleri testi"""
    response = authenticated_client.get('/monitoring', follow_redirects=True)
    assert response.status_code == 200
    
    # Dashboard'un önemli bileşenlerini kontrol et
    content = response.data.decode('utf-8').lower()
    
    # Log viewer, health status, stats gibi bileşenler olmalı
    assert 'log' in content or 'health' in content or 'stat' in content


@pytest.mark.integration
def test_monitoring_health_database_component(authenticated_client):
    """Database component health testi"""
    response = authenticated_client.get('/monitoring/api/health')
    data = json.loads(response.data)
    
    health = data['data']
    assert 'components' in health
    assert 'database' in health['components']
    
    # Database status healthy olmalı
    db_status = health['components']['database']
    assert db_status in ['healthy', 'warning', 'unhealthy']


@pytest.mark.integration
def test_monitoring_health_logs_component(authenticated_client):
    """Logs component health testi"""
    response = authenticated_client.get('/monitoring/api/health')
    data = json.loads(response.data)
    
    health = data['data']
    assert 'components' in health
    assert 'logs' in health['components']
    
    # Logs status healthy olmalı
    logs_status = health['components']['logs']
    assert logs_status in ['healthy', 'warning', 'unhealthy']


@pytest.mark.integration
def test_monitoring_disk_usage_info(authenticated_client):
    """Disk usage bilgisi testi"""
    response = authenticated_client.get('/monitoring/api/health')
    data = json.loads(response.data)
    
    health = data['data']
    assert 'disk_usage' in health
    
    disk_usage = health['disk_usage']
    if disk_usage:
        assert 'free_percent' in disk_usage
        assert 'total_gb' in disk_usage
        assert 'used_gb' in disk_usage


@pytest.mark.integration
def test_monitoring_log_files_info(authenticated_client):
    """Log files bilgisi testi"""
    response = authenticated_client.get('/monitoring/api/stats')
    data = json.loads(response.data)
    
    stats = data['data']
    assert 'log_files' in stats
    
    log_files = stats['log_files']
    # Log files bir dict olmalı
    assert isinstance(log_files, dict)


@pytest.mark.integration
def test_monitoring_recent_errors(authenticated_client):
    """Son hatalar bilgisi testi"""
    response = authenticated_client.get('/monitoring/api/stats')
    data = json.loads(response.data)
    
    stats = data['data']
    assert 'recent_errors' in stats
    
    recent_errors = stats['recent_errors']
    # Recent errors bir list olmalı
    assert isinstance(recent_errors, list)


@pytest.mark.integration
def test_monitoring_stats_counts(authenticated_client):
    """Monitoring sayısal değerleri testi"""
    response = authenticated_client.get('/monitoring/api/stats')
    data = json.loads(response.data)
    
    stats = data['data']
    
    # Tüm sayısal değerler non-negative olmalı
    assert stats['total_logs'] >= 0
    assert stats['error_count'] >= 0
    assert stats['warning_count'] >= 0
    assert stats['critical_count'] >= 0
    assert stats['security_count'] >= 0


@pytest.mark.integration
def test_monitoring_logs_pagination(authenticated_client):
    """Logs pagination testi"""
    # Farklı line sayıları ile test et
    for lines in [5, 10, 20, 50]:
        response = authenticated_client.get(f'/monitoring/api/logs?file=e_cuzdan&lines={lines}')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert 'data' in data
        assert len(data['data']['logs']) <= lines


@pytest.mark.integration
def test_monitoring_logs_invalid_file(authenticated_client):
    """Geçersiz log dosyası testi"""
    response = authenticated_client.get('/monitoring/api/logs?file=invalid_file&lines=10')
    assert response.status_code == 200
    
    data = json.loads(response.data)
    # Hata durumunda success false olabilir
    # Ama API hata vermemeli
    assert 'success' in data


@pytest.mark.integration
def test_monitoring_alerts_config_structure(authenticated_client):
    """Alerts config yapısı testi"""
    response = authenticated_client.get('/monitoring/api/alerts/config')
    data = json.loads(response.data)
    
    config = data['data']
    # Config bir dict olmalı
    assert isinstance(config, dict)


@pytest.mark.integration
def test_monitoring_dashboard_responsive(authenticated_client):
    """Dashboard responsive tasarım testi"""
    response = authenticated_client.get('/monitoring', follow_redirects=True)
    assert response.status_code == 200
    
    content = response.data.decode('utf-8')
    
    # Responsive tasarım için viewport meta tag'i olmalı
    assert 'viewport' in content.lower() or 'responsive' in content.lower()
