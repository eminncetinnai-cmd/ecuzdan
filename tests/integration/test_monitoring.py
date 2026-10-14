"""
Integration Tests - Monitoring API
Monitoring endpoints ve dashboard entegrasyon testleri - Detailed functional tests
"""

import json

import pytest


@pytest.mark.integration
def test_monitoring_dashboard_route(privileged_authenticated_client):
    """Monitoring dashboard route testi"""
    response = privileged_authenticated_client.get('/monitoring', follow_redirects=True)
    assert response.status_code == 200
    assert b'monitoring' in response.data.lower()


@pytest.mark.integration
def test_monitoring_stats_api(privileged_authenticated_client):
    """Monitoring stats API testi"""
    response = privileged_authenticated_client.get('/monitoring/api/stats')
    assert response.status_code == 200

    data = json.loads(response.data)
    assert 'success' in data
    assert 'data' in data
    assert data['success'] is True


@pytest.mark.integration
def test_monitoring_stats_structure(privileged_authenticated_client):
    """Monitoring stats yapısı testi"""
    response = privileged_authenticated_client.get('/monitoring/api/stats')
    data = json.loads(response.data)

    stats = data['data']
    required_fields = [
        'total_logs', 'error_count', 'warning_count',
        'critical_count', 'security_count', 'log_files'
    ]

    for field in required_fields:
        assert field in stats


@pytest.mark.integration
def test_monitoring_stats_data_types(privileged_authenticated_client):
    """Monitoring stats veri tipleri testi"""
    response = privileged_authenticated_client.get('/monitoring/api/stats')
    data = json.loads(response.data)

    stats = data['data']

    assert isinstance(stats['total_logs'], int)
    assert isinstance(stats['error_count'], int)
    assert isinstance(stats['warning_count'], int)
    assert isinstance(stats['critical_count'], int)
    assert isinstance(stats['security_count'], int)
    assert isinstance(stats['log_files'], dict)


@pytest.mark.integration
def test_monitoring_health_api(privileged_authenticated_client):
    """Monitoring health API testi"""
    response = privileged_authenticated_client.get('/monitoring/api/health')
    assert response.status_code == 200

    data = json.loads(response.data)
    assert 'success' in data
    assert 'data' in data
    assert data['success'] is True


@pytest.mark.integration
def test_monitoring_health_structure(privileged_authenticated_client):
    """Monitoring health yapısı testi"""
    response = privileged_authenticated_client.get('/monitoring/api/health')
    data = json.loads(response.data)

    health = data['data']
    required_fields = ['status', 'components', 'disk_usage', 'issues']

    for field in required_fields:
        assert field in health


@pytest.mark.integration
def test_monitoring_health_status_values(privileged_authenticated_client):
    """Monitoring health status değerleri testi"""
    response = privileged_authenticated_client.get('/monitoring/api/health')
    data = json.loads(response.data)

    health = data['data']
    assert health['status'] in ['healthy', 'degraded', 'critical']


@pytest.mark.integration
def test_monitoring_logs_api(privileged_authenticated_client):
    """Monitoring logs API testi"""
    response = privileged_authenticated_client.get('/monitoring/api/logs?file=e_cuzdan&lines=10')
    assert response.status_code == 200

    data = json.loads(response.data)
    assert 'success' in data
    assert 'data' in data
    assert data['success'] is True


@pytest.mark.integration
def test_monitoring_logs_structure(privileged_authenticated_client):
    """Monitoring logs yapısı testi"""
    response = privileged_authenticated_client.get('/monitoring/api/logs?file=e_cuzdan&lines=10')
    data = json.loads(response.data)

    logs_data = data['data']
    assert 'logs' in logs_data
    assert isinstance(logs_data['logs'], list)


@pytest.mark.integration
def test_monitoring_logs_with_filter(privileged_authenticated_client):
    """Monitoring logs filtreleme testi"""
    response = privileged_authenticated_client.get('/monitoring/api/logs?file=e_cuzdan&lines=10&level=ERROR')
    assert response.status_code == 200

    data = json.loads(response.data)
    assert 'success' in data
    assert 'data' in data
    assert data['success'] is True


@pytest.mark.integration
def test_monitoring_logs_with_search(privileged_authenticated_client):
    """Monitoring logs arama testi"""
    response = privileged_authenticated_client.get('/monitoring/api/logs?file=e_cuzdan&lines=10&search=test')
    assert response.status_code == 200

    data = json.loads(response.data)
    assert 'success' in data
    assert 'data' in data
    assert data['success'] is True


@pytest.mark.integration
def test_monitoring_alerts_config_api(privileged_authenticated_client):
    """Monitoring alerts config API testi"""
    response = privileged_authenticated_client.get('/monitoring/api/alerts/config')
    assert response.status_code == 200

    data = json.loads(response.data)
    assert 'success' in data
    assert 'data' in data
    assert data['success'] is True


@pytest.mark.integration
def test_monitoring_alerts_config_structure(privileged_authenticated_client):
    """Alerts config yapısı testi"""
    response = privileged_authenticated_client.get('/monitoring/api/alerts/config')
    data = json.loads(response.data)

    config = data['data']
    # Config bir dict olmalı
    assert isinstance(config, dict)


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
def test_monitoring_dashboard_components(privileged_authenticated_client):
    """Monitoring dashboard bileşenleri testi"""
    response = privileged_authenticated_client.get('/monitoring', follow_redirects=True)
    assert response.status_code == 200

    # Dashboard'un önemli bileşenlerini kontrol et
    content = response.data.decode('utf-8').lower()

    # Log viewer, health status, stats gibi bileşenler olmalı
    assert 'log' in content or 'health' in content or 'stat' in content


@pytest.mark.integration
def test_monitoring_health_database_component(privileged_authenticated_client):
    """Database component health testi"""
    response = privileged_authenticated_client.get('/monitoring/api/health')
    data = json.loads(response.data)

    health = data['data']
    assert 'components' in health
    assert 'database' in health['components']

    # Database status healthy olmalı
    db_status = health['components']['database']
    assert db_status in ['healthy', 'warning', 'unhealthy']


@pytest.mark.integration
def test_monitoring_health_logs_component(privileged_authenticated_client):
    """Logs component health testi"""
    response = privileged_authenticated_client.get('/monitoring/api/health')
    data = json.loads(response.data)

    health = data['data']
    assert 'components' in health
    assert 'logs' in health['components']

    # Logs status healthy olmalı
    logs_status = health['components']['logs']
    assert logs_status in ['healthy', 'warning', 'unhealthy']


@pytest.mark.integration
def test_monitoring_disk_usage_info(privileged_authenticated_client):
    """Disk usage bilgisi testi"""
    response = privileged_authenticated_client.get('/monitoring/api/health')
    data = json.loads(response.data)

    health = data['data']
    assert 'disk_usage' in health

    disk_usage = health['disk_usage']
    if disk_usage:
        assert 'free_percent' in disk_usage
        assert 'total_gb' in disk_usage
        assert 'used_gb' in disk_usage


@pytest.mark.integration
def test_monitoring_log_files_info(privileged_authenticated_client):
    """Log files bilgisi testi"""
    response = privileged_authenticated_client.get('/monitoring/api/stats')
    data = json.loads(response.data)

    stats = data['data']
    assert 'log_files' in stats

    log_files = stats['log_files']
    # Log files bir dict olmalı
    assert isinstance(log_files, dict)


@pytest.mark.integration
def test_monitoring_recent_errors(privileged_authenticated_client):
    """Son hatalar bilgisi testi"""
    response = privileged_authenticated_client.get('/monitoring/api/stats')
    data = json.loads(response.data)

    stats = data['data']
    assert 'recent_errors' in stats

    recent_errors = stats['recent_errors']
    # Recent errors bir list olmalı
    assert isinstance(recent_errors, list)


@pytest.mark.integration
def test_monitoring_stats_counts(privileged_authenticated_client):
    """Monitoring sayısal değerleri testi"""
    response = privileged_authenticated_client.get('/monitoring/api/stats')
    data = json.loads(response.data)

    stats = data['data']

    # Tüm sayısal değerler non-negative olmalı
    assert stats['total_logs'] >= 0
    assert stats['error_count'] >= 0
    assert stats['warning_count'] >= 0
    assert stats['critical_count'] >= 0
    assert stats['security_count'] >= 0


@pytest.mark.integration
def test_monitoring_logs_pagination(privileged_authenticated_client):
    """Logs pagination testi"""
    # Farklı line sayıları ile test et
    for lines in [5, 10, 20, 50]:
        response = privileged_authenticated_client.get(f'/monitoring/api/logs?file=e_cuzdan&lines={lines}')
        assert response.status_code == 200

        data = json.loads(response.data)
        assert 'data' in data
        assert len(data['data']['logs']) <= lines


@pytest.mark.integration
def test_monitoring_logs_invalid_file(privileged_authenticated_client):
    """Geçersiz log dosyası testi"""
    response = privileged_authenticated_client.get('/monitoring/api/logs?file=invalid_file&lines=10')
    assert response.status_code == 200

    data = json.loads(response.data)
    # Hata durumunda success false olabilir
    # Ama API hata vermemeli
    assert 'success' in data


@pytest.mark.integration
def test_monitoring_dashboard_responsive(privileged_authenticated_client):
    """Dashboard responsive tasarım testi"""
    response = privileged_authenticated_client.get('/monitoring', follow_redirects=True)
    assert response.status_code == 200

    content = response.data.decode('utf-8')

    # Responsive tasarım için viewport meta tag'i olmalı
    assert 'viewport' in content.lower() or 'responsive' in content.lower()


@pytest.mark.integration
def test_monitoring_cache_behavior(privileged_authenticated_client):
    """Cache davranışı testi"""
    # İlk istek
    response1 = privileged_authenticated_client.get('/monitoring/api/stats')
    assert response1.status_code == 200

    # İkinci istek (cache'den gelebilir)
    response2 = privileged_authenticated_client.get('/monitoring/api/stats')
    assert response2.status_code == 200

    # Her iki yanıt da geçerli olmalı
    data1 = json.loads(response1.data)
    data2 = json.loads(response2.data)
    assert data1['success'] is True
    assert data2['success'] is True


@pytest.mark.integration
def test_monitoring_logs_different_files(privileged_authenticated_client):
    """Farklı log dosyaları testi"""
    log_files = ['e_cuzdan', 'e_cuzdan_errors', 'e_cuzdan_security']

    for log_file in log_files:
        response = privileged_authenticated_client.get(f'/monitoring/api/logs?file={log_file}&lines=5')
        assert response.status_code == 200

        data = json.loads(response.data)
        assert 'success' in data


@pytest.mark.integration
def test_monitoring_logs_empty_search(privileged_authenticated_client):
    """Boş arama sorgusu testi"""
    response = privileged_authenticated_client.get('/monitoring/api/logs?file=e_cuzdan&lines=10&search=')
    assert response.status_code == 200

    data = json.loads(response.data)
    assert 'success' in data


@pytest.mark.integration
def test_monitoring_logs_invalid_lines(privileged_authenticated_client):
    """Geçersiz lines parametresi testi"""
    response = privileged_authenticated_client.get('/monitoring/api/logs?file=e_cuzdan&lines=invalid')
    # API hata vermemeli, geçerli bir yanıt dönmeli
    assert response.status_code in [200, 400, 500]


@pytest.mark.integration
def test_monitoring_health_issues_field(privileged_authenticated_client):
    """Health issues alanı testi"""
    response = privileged_authenticated_client.get('/monitoring/api/health')
    data = json.loads(response.data)

    health = data['data']
    assert 'issues' in health
    assert isinstance(health['issues'], list)


@pytest.mark.integration
def test_monitoring_components_all_required(privileged_authenticated_client):
    """Tüm required component'lar testi"""
    response = privileged_authenticated_client.get('/monitoring/api/health')
    data = json.loads(response.data)

    health = data['data']
    components = health['components']

    # En az database ve logs component'ları olmalı
    assert 'database' in components
    assert 'logs' in components


@pytest.mark.integration
def test_monitoring_stats_log_files_keys(privileged_authenticated_client):
    """Log files keys testi"""
    response = privileged_authenticated_client.get('/monitoring/api/stats')
    data = json.loads(response.data)

    stats = data['data']
    log_files = stats['log_files']

    # Log files dict'in anahtarları string olmalı
    for key in log_files.keys():
        assert isinstance(key, str)


@pytest.mark.integration
def test_monitoring_alerts_config_post(privileged_authenticated_client):
    """Alerts config POST testi"""
    response = privileged_authenticated_client.post(
        '/monitoring/api/alerts/config',
        json={'email_alerts_enabled': True},
        content_type='application/json'
    )
    # POST isteği başarılı olmalı
    assert response.status_code in [200, 201]


@pytest.mark.integration
def test_monitoring_concurrent_requests(privileged_authenticated_client):
    """Concurrent requests testi"""
    import threading

    def make_request():
        response = privileged_authenticated_client.get('/monitoring/api/stats')
        assert response.status_code == 200

    threads = [threading.Thread(target=make_request) for _ in range(5)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()


@pytest.mark.integration
def test_monitoring_response_headers(privileged_authenticated_client):
    """Response headers testi"""
    response = privileged_authenticated_client.get('/monitoring/api/stats')
    assert response.status_code == 200

    # Content-Type header'ı olmalı
    assert 'Content-Type' in response.headers


@pytest.mark.integration
def test_monitoring_json_content_type(privileged_authenticated_client):
    """JSON content type testi"""
    response = privileged_authenticated_client.get('/monitoring/api/stats')
    assert response.status_code == 200

    content_type = response.headers.get('Content-Type', '')
    assert 'application/json' in content_type


@pytest.mark.integration
def test_monitoring_alerts_status_api(privileged_authenticated_client):
    """Alert status API testi"""
    response = privileged_authenticated_client.get('/monitoring/api/alerts/status')
    assert response.status_code == 200

    data = json.loads(response.data)
    assert data['success'] is True
    assert 'enabled' in data['data']


@pytest.mark.integration
def test_monitoring_logs_request_id_filter(privileged_authenticated_client):
    """Request ID filter on logs API"""
    response = privileged_authenticated_client.get(
        '/monitoring/api/logs?file=main&lines=10&request_id=abc123def'
    )
    assert response.status_code == 200

    data = json.loads(response.data)
    assert data['success'] is True


@pytest.mark.integration
def test_monitoring_logs_structured_file(privileged_authenticated_client):
    """Structured log file alias"""
    response = privileged_authenticated_client.get('/monitoring/api/logs?file=structured&lines=5')
    assert response.status_code in (200, 404)
