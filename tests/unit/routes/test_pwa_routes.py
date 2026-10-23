"""
Unit tests for Progressive Web App (PWA) routes and assets.
Verifies Web App Manifest, Service Worker, Apple Touch Icons,
Offline fallback page, and 24/7 Keep-Alive heartbeat.
"""

import json
import os
import pytest
from app import app


@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


def test_manifest_endpoint_and_structure(client):
    """Test that /manifest.json returns valid PWA manifest data without auth redirect."""
    response = client.get('/manifest.json')
    assert response.status_code == 200
    assert 'application/manifest+json' in response.content_type

    data = json.loads(response.get_data(as_text=True))
    assert data.get('display') == 'standalone'
    assert data.get('start_url') == '/?source=pwa'
    assert 'icons' in data and len(data['icons']) >= 2

    icon_srcs = [i['src'] for i in data['icons']]
    assert '/static/pwa-icon-192.png' in icon_srcs
    assert '/static/pwa-icon-512.png' in icon_srcs


def test_service_worker_endpoint_and_headers(client):
    """Test that /sw.js has Service-Worker-Allowed header allowing root scope."""
    response = client.get('/sw.js')
    assert response.status_code == 200
    assert 'javascript' in response.content_type
    assert response.headers.get('Service-Worker-Allowed') == '/'
    assert 'no-cache' in response.headers.get('Cache-Control', '')


def test_apple_touch_icon_endpoints(client):
    """Test that Apple touch icons return valid PNG images."""
    for path in ['/apple-touch-icon.png', '/apple-touch-icon-precomposed.png']:
        response = client.get(path)
        assert response.status_code == 200
        assert 'image/png' in response.content_type


def test_offline_fallback_page(client):
    """Test that /offline renders the offline workspace without requiring authentication."""
    response = client.get('/offline')
    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert 'Çevrimdışı Çalışma Alanı' in html
    assert 'offlineWorkspaceQueueCount' in html


def test_keepalive_heartbeat_api(client):
    """Test that /api/keepalive returns instant 200 JSON status for Render keep-alive."""
    response = client.get('/api/keepalive')
    assert response.status_code == 200
    assert response.is_json
    data = response.get_json()
    assert data.get('status') == 'alive'
    assert 'timestamp' in data


def test_pwa_icon_files_exist_on_disk():
    """Verify that all generated Apple & PWA icons exist in the static directory."""
    static_dir = os.path.join(app.root_path, 'static')
    expected_files = [
        'apple-touch-icon.png',
        'apple-touch-icon-180x180.png',
        'apple-touch-icon-167x167.png',
        'apple-touch-icon-152x152.png',
        'apple-touch-icon-120x120.png',
        'pwa-icon-192.png',
        'pwa-icon-512.png',
        'pwa-icon-maskable.png',
        'favicon-32x32.png',
        'manifest.json',
        'sw.js',
        'js/haptics.js',
        'js/pull-to-refresh.js',
        'js/biometrics.js',
        'js/web-push-manager.js',
        'js/offline-outbox.js',
    ]
    for filename in expected_files:
        filepath = os.path.join(static_dir, filename)
        assert os.path.isfile(filepath), f"Missing required PWA asset on disk: {filename}"
        assert os.path.getsize(filepath) > 0, f"PWA asset is empty: {filename}"
