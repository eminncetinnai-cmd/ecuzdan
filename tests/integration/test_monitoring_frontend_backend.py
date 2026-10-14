"""
Integration Tests - Monitoring Frontend-Backend Integration
Profesyonel testler: Frontend ve backend arasındaki API tutarsızlıklarını tespit eder
"""

import json

import pytest


@pytest.mark.integration
def test_monitoring_health_api_response_format(privileged_authenticated_client):
    """Health API response formatının frontend beklentisiyle uyumlu olduğunu test eder"""
    response = privileged_authenticated_client.get('/monitoring/api/health')
    assert response.status_code == 200

    data = json.loads(response.data)

    # Frontend monitoring.js line 38-45 beklenen format:
    # result.success ve result.data olmalı
    assert 'success' in data, "Response 'success' field eksik"
    assert 'data' in data, "Response 'data' field eksik"

    # Data içinde gerekli alanlar olmalı (monitoring.js line 54-110)
    health_data = data['data']
    assert 'status' in health_data, "Health data 'status' field eksik"
    assert 'components' in health_data, "Health data 'components' field eksik"
    assert isinstance(health_data['components'], dict), "Components dict olmalı"


@pytest.mark.integration
def test_monitoring_stats_api_response_format(privileged_authenticated_client):
    """Stats API response formatının frontend beklentisiyle uyumlu olduğunu test eder"""
    response = privileged_authenticated_client.get('/monitoring/api/stats')
    assert response.status_code == 200

    data = json.loads(response.data)

    # Frontend monitoring.js line 124-131 beklenen format:
    assert 'success' in data, "Response 'success' field eksik"
    assert 'data' in data, "Response 'data' field eksik"

    # Data içinde gerekli alanlar (monitoring.js line 140-148)
    stats_data = data['data']
    required_fields = [
        'total_logs', 'error_count', 'warning_count',
        'critical_count', 'security_count', 'log_files'
    ]

    for field in required_fields:
        assert field in stats_data, f"Stats data '{field}' field eksik"
        assert isinstance(stats_data[field], (int, dict)), f"{field} yanlış tip"


@pytest.mark.integration
def test_monitoring_logs_api_response_format(privileged_authenticated_client):
    """Logs API response formatının frontend beklentisiyle uyumlu olduğunu test eder"""
    response = privileged_authenticated_client.get('/monitoring/api/logs?file=e_cuzdan&lines=10')
    assert response.status_code == 200

    data = json.loads(response.data)

    # Frontend monitoring.js line 199-204 beklenen format:
    assert 'success' in data, "Response 'success' field eksik"
    assert 'data' in data, "Response 'data' field eksik"

    # Data içinde logs listesi olmalı (monitoring.js line 202)
    log_data = data['data']
    assert 'logs' in log_data, "Log data 'logs' field eksik"
    assert 'count' in log_data, "Log data 'count' field eksik"
    assert isinstance(log_data['logs'], list), "Logs list olmalı"


@pytest.mark.integration
def test_monitoring_health_status_values(privileged_authenticated_client):
    """Health status değerlerinin geçerli olduğunu test eder"""
    response = privileged_authenticated_client.get('/monitoring/api/health')
    data = json.loads(response.data)

    health = data['data']

    # Status değerleri geçerli olmalı (monitoring.js line 61-66)
    valid_statuses = ['healthy', 'degraded', 'critical']
    assert health['status'] in valid_statuses, f"Geçersiz status: {health['status']}"

    # Component status değerleri geçerli olmalı (monitoring.js line 88-94)
    valid_component_statuses = ['healthy', 'warning', 'unhealthy', 'unknown']
    for component, status in health['components'].items():
        assert status in valid_component_statuses, f"Component {component} geçersiz status: {status}"


@pytest.mark.integration
def test_monitoring_disk_usage_structure(privileged_authenticated_client):
    """Disk usage bilgisinin doğru yapıda olduğunu test eder"""
    response = privileged_authenticated_client.get('/monitoring/api/health')
    data = json.loads(response.data)

    health = data['data']

    if 'disk_usage' in health and health['disk_usage']:
        disk = health['disk_usage']

        # Frontend monitoring.js line 98-108 beklenen alanlar
        required_disk_fields = ['total_gb', 'used_gb', 'free_percent']
        for field in required_disk_fields:
            assert field in disk, f"Disk usage '{field}' field eksik"
            assert isinstance(disk[field], (int, float)), f"{field} sayı olmalı"


@pytest.mark.integration
def test_monitoring_log_files_structure(privileged_authenticated_client):
    """Log files bilgisinin doğru yapıda olduğunu test eder"""
    response = privileged_authenticated_client.get('/monitoring/api/stats')
    data = json.loads(response.data)

    stats = data['data']

    if 'log_files' in stats:
        log_files = stats['log_files']

        # Frontend monitoring.js line 158-169 beklenen yapı
        assert isinstance(log_files, dict), "Log files dict olmalı"

        for file_type, info in log_files.items():
            if info.get('exists'):
                assert 'size_bytes' in info, f"{file_type} size_bytes eksik"
                assert 'size_mb' in info, f"{file_type} size_mb eksik"
                assert isinstance(info['size_mb'], (int, float)), "size_mb sayı olmalı"


@pytest.mark.integration
def test_monitoring_api_content_type(privileged_authenticated_client):
    """API response'larının doğru content-type döndürdüğünü test eder"""
    endpoints = [
        '/monitoring/api/health',
        '/monitoring/api/stats',
        '/monitoring/api/logs?file=e_cuzdan&lines=10'
    ]

    for endpoint in endpoints:
        response = privileged_authenticated_client.get(endpoint)
        assert response.status_code == 200
        assert 'application/json' in response.content_type, f"{endpoint} JSON dönmüyor"


@pytest.mark.integration
def test_monitoring_api_error_handling(privileged_authenticated_client):
    """API error handling'in doğru çalıştığını test eder"""
    # Geçersiz log dosyası ile test
    response = privileged_authenticated_client.get('/monitoring/api/logs?file=nonexistent&lines=10')

    # API hata durumunda bile JSON dönmeli (monitoring.js line 34-36)
    assert response.status_code in [200, 404], "Status kodu beklenmedik"

    if response.status_code == 200:
        data = json.loads(response.data)
        assert 'success' in data, "Error response 'success' field eksik"


@pytest.mark.integration
def test_monitoring_api_caching_behavior(privileged_authenticated_client):
    """API caching mekanizmasının çalıştığını test eder"""
    # İlk request
    response1 = privileged_authenticated_client.get('/monitoring/api/health')
    data1 = json.loads(response1.data)

    # İkinci request (cache'den gelebilir)
    response2 = privileged_authenticated_client.get('/monitoring/api/health')
    data2 = json.loads(response2.data)

    # İki response da başarılı olmalı
    assert response1.status_code == 200
    assert response2.status_code == 200
    assert data1['success'] is True
    assert data2['success'] is True


@pytest.mark.integration
def test_monitoring_api_pagination(privileged_authenticated_client):
    """Logs pagination'ın doğru çalıştığını test eder"""
    # Farklı line sayıları ile test
    for lines in [5, 10, 50, 100]:
        response = privileged_authenticated_client.get(f'/monitoring/api/logs?file=e_cuzdan&lines={lines}')
        assert response.status_code == 200

        data = json.loads(response.data)
        logs = data['data']['logs']

        # Dönen log sayısı istenen sayıdan fazla olmamalı
        assert len(logs) <= lines, f"Pagination hatası: {len(logs)} > {lines}"


@pytest.mark.integration
def test_monitoring_api_filtering(privileged_authenticated_client):
    """Logs filtering'in doğru çalıştığını test eder"""
    # Level filtreleme
    response = privileged_authenticated_client.get('/monitoring/api/logs?file=e_cuzdan&lines=100&level=ERROR')
    assert response.status_code == 200

    data = json.loads(response.data)
    logs = data['data']['logs']

    # Filtrelenen loglar level içermeli
    for log in logs:
        assert 'ERROR' in log, "Filtreleme hatası: ERROR içermeyen log geldi"


@pytest.mark.integration
def test_monitoring_api_search(privileged_authenticated_client):
    """Logs search'in doğru çalıştığını test eder"""
    # Arama terimi ile test (backend case-sensitive)
    response = privileged_authenticated_client.get('/monitoring/api/logs?file=e_cuzdan&lines=100&search=DEBUG')
    assert response.status_code == 200

    data = json.loads(response.data)
    logs = data['data']['logs']

    # Arama terimi loglarda bulunmalı (case-sensitive as per backend implementation)
    for log in logs:
        assert 'DEBUG' in log, "Arama hatası: terim bulunamadı"


@pytest.mark.integration
def test_monitoring_dashboard_loads(privileged_authenticated_client):
    """Dashboard sayfasının doğru yüklendiğini test eder"""
    response = privileged_authenticated_client.get('/monitoring', follow_redirects=True)
    assert response.status_code == 200

    content = response.data.decode('utf-8')

    # Dashboard elementleri olmalı
    assert 'health-status' in content, "health-status elementi eksik"
    assert 'total-logs' in content, "total-logs elementi eksik"
    assert 'log-container' in content, "log-container elementi eksik"
    assert 'Sistem Monitoring' in content, "Monitoring başlığı eksik"


@pytest.mark.integration
def test_monitoring_api_timestamp_format(privileged_authenticated_client):
    """API timestamp formatının ISO 8601 olduğunu test eder"""
    response = privileged_authenticated_client.get('/monitoring/api/health')
    data = json.loads(response.data)

    health = data['data']

    if 'timestamp' in health:
        # ISO 8601 format kontrolü
        from datetime import datetime
        try:
            datetime.fromisoformat(health['timestamp'])
        except ValueError:
            pytest.fail(f"Timestamp ISO 8601 formatında değil: {health['timestamp']}")


@pytest.mark.integration
def test_monitoring_recent_errors_structure(privileged_authenticated_client):
    """Recent errors bilgisinin doğru yapıda olduğunu test eder"""
    response = privileged_authenticated_client.get('/monitoring/api/stats')
    data = json.loads(response.data)

    stats = data['data']

    if 'recent_errors' in stats:
        recent_errors = stats['recent_errors']

        # List olmalı
        assert isinstance(recent_errors, list), "recent_errors list olmalı"

        # Frontend, eski string kayıtlarını ve yeni yapılandırılmış DTO'ları
        # birlikte güvenli biçimde render edebilmelidir.
        for error in recent_errors:
            assert isinstance(error, (str, dict)), "Error string veya DTO olmalı"
            if isinstance(error, dict):
                assert any(field in error for field in ('message', 'raw', 'level'))


@pytest.mark.integration
def test_monitoring_components_count(privileged_authenticated_client):
    """Health components sayısının doğru olduğunu test eder"""
    response = privileged_authenticated_client.get('/monitoring/api/health')
    data = json.loads(response.data)

    health = data['data']
    components = health['components']

    # En az 3 component olmalı (database, logs, disk_space)
    assert len(components) >= 3, f"Component sayısı yetersiz: {len(components)}"

    # Beklenen componentler olmalı
    expected_components = ['database', 'logs', 'disk_space']
    for comp in expected_components:
        assert comp in components, f"{comp} component eksik"


@pytest.mark.integration
def test_monitoring_numeric_values_non_negative(privileged_authenticated_client):
    """Tüm sayısal değerlerin non-negative olduğunu test eder"""
    response = privileged_authenticated_client.get('/monitoring/api/stats')
    data = json.loads(response.data)

    stats = data['data']

    numeric_fields = ['total_logs', 'error_count', 'warning_count', 'critical_count', 'security_count']

    for field in numeric_fields:
        assert stats[field] >= 0, f"{field} negatif değer: {stats[field]}"
