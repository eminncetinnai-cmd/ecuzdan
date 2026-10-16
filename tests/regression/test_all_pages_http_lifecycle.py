"""
Master HTTP Lifecycle & Route Resilience Test Suite (test_all_pages_http_lifecycle.py)

Programdaki tüm temel sayfaların ve uç noktaların HTTP yaşam döngüsünü doğrular:
  - 200 OK: Tüm arayüz ve raporlama sayfalarının sorunsuz yüklenmesi (0 adet 500 hatası)
  - 302/401: Kimlik doğrulanmamış isteklerin güvenli şekilde login'e yönlendirilmesi
  - 403: Yetkisiz kullanıcıların admin/izleme alanlarından engellenmesi
  - 404: Var olmayan sayfa ve kaynaklarda kontrollü hata sayfası gösterimi
  - 500: Beklenmeyen sistem hatalarında güvenli (fail-closed) hata sayfası ve sıfır sızıntı
  - 429: Aşırı istek durumunda kontrollü yanıt ve Retry-After başlığı
"""

from __future__ import annotations

from unittest.mock import patch

import pytest
from flask import abort


@pytest.mark.regression
def test_all_core_ui_pages_return_200_and_never_500(authenticated_client):
    """Kullanıcı arayüzündeki tüm temel sayfaların 200 OK döndüğünü ve hiçbirinin 500 vermediğini doğrular."""
    core_pages = [
        ('/', 'Dashboard / Ana Sayfa'),
        ('/monthly_dashboard', 'Aylık Konsolide Özet'),
        ('/transactions', 'İşlem Geçmişi'),
        ('/plans', 'Düzenli İşlemler & Planlar'),
        ('/payment_calendar', 'Ödeme Takvimi'),
        ('/assets', 'Varlıklar Listesi'),
        ('/assets_view', 'Varlık Görünümü'),
        ('/assets_management', 'Varlık Yönetimi'),
        ('/investment_performance', 'Yatırım Getirisi & Performans'),
        ('/analysis', 'Finansal Analiz & Sağlık'),
        ('/financial_freedom', 'Finansal Özgürlük (FIRE)'),
        ('/strategy', 'Strateji & Gelecek Simülasyonu'),
        ('/financial_dashboard', 'Finans & Piyasa Özeti'),
        ('/global-ratios', 'Küresel Rasyolar Dashboard'),
        ('/central-bank-reserves', 'Merkez Bankası Rezervleri'),
        ('/logbook/', 'Yatırım Günlüğü & Notlar'),
        ('/categories', 'Kategori Yönetimi'),
        ('/notifications', 'Bildirim Merkezi'),
        ('/profile', 'Yatırımcı Profili'),
        ('/profile/start', 'Yatırımcı Anketi (Wizard)'),
        ('/settings', 'Sistem & Hesap Ayarları'),
        ('/user_guide', 'Kullanım Kılavuzu & Rehber'),
        ('/financial_education', 'Finansal Eğitim & Formüller'),
        ('/storage-health/', 'Depolama Sağlığı & Bakım'),
    ]

    failed_pages = []

    for path, name in core_pages:
        response = authenticated_client.get(path, follow_redirects=True)
        status = response.status_code

        # Asla 500 dönmemeli
        if status == 500:
            failed_pages.append(f"{path} ({name}) -> HTTP 500 Internal Server Error")
        elif status != 200:
            failed_pages.append(f"{path} ({name}) -> Beklenen 200 yerine HTTP {status} döndü")

        # HTML içeriği boş veya hata sızıntısı olmamalı
        html = response.get_data(as_text=True)
        assert len(html) > 50, f"{path} boş sayfa döndürdü!"
        assert "Traceback (most recent call last)" not in html, f"{path} stack trace sızdırdı!"

    assert not failed_pages, "Aşağıdaki sayfalarda HTTP hatası tespit edildi:\n" + "\n".join(failed_pages)


@pytest.mark.regression
def test_admin_and_monitoring_pages_for_privileged_admin(privileged_authenticated_client):
    """Yetkili yönetici için Admin ve İzleme sayfalarının 200 OK döndüğünü doğrular."""
    admin_pages = [
        ('/admin/', 'Admin Ana Sayfası'),
        ('/admin/users', 'Kullanıcı Yönetimi'),
        ('/admin/tenants', 'Tenant Yönetimi'),
        ('/admin/design_system', 'Tasarım Sistemi Kataloğu'),
        ('/admin/audit', 'Admin Denetim Günlüğü'),
        ('/monitoring/', 'İzleme & Log Dashboard'),
    ]

    failed_pages = []

    for path, name in admin_pages:
        response = privileged_authenticated_client.get(path, follow_redirects=True)
        status = response.status_code

        if status == 500:
            failed_pages.append(f"{path} ({name}) -> HTTP 500")
        elif status != 200:
            failed_pages.append(f"{path} ({name}) -> Beklenen 200 yerine HTTP {status}")

    assert not failed_pages, "Admin sayfalarında hata:\n" + "\n".join(failed_pages)


@pytest.mark.regression
def test_http_404_not_found_handling(client):
    """Var olmayan rotalarda uygulamanın çökmeyip kontrollü 404 sayfası (UI) veya JSON (API) döndüğünü doğrular."""
    # 1. Var olmayan UI sayfası -> HTML 404
    res_ui = client.get('/kesinlikle-boyle-bir-sayfa-yok-404')
    assert res_ui.status_code == 404
    assert not res_ui.is_json
    html = res_ui.get_data(as_text=True)
    assert '404' in html
    assert 'Aradığınız sayfa bulunamadı' in html or 'bulunamadı' in html.lower()
    assert 'Traceback (most recent call last)' not in html

    # 2. Var olmayan derin URL -> 404
    res_deep = client.get('/transactions/alt/detay/99999/olmayan')
    assert res_deep.status_code == 404

    # 3. Var olmayan API endpoint'i -> JSON 404
    res_api = client.get('/api/non-existent-endpoint-xyz-987')
    assert res_api.status_code == 404
    assert res_api.is_json
    api_data = res_api.get_json()
    assert api_data.get('success') is False
    assert api_data.get('code') == 404
    assert 'error' in api_data


@pytest.mark.regression
def test_http_500_internal_server_error_and_no_leak(client):
    """Sunucu içi istisna fırlatıldığında UI için 500 HTML sayfası, API için 500 JSON döndüğünü doğrular."""
    # 1. UI 500 hatası -> error.html
    with patch('routes.auth.get_daily_insight', side_effect=RuntimeError("Test amaçlı tetiklenen simüle edilmiş kritik hata")):
        response = client.get('/login')

    assert response.status_code == 500
    assert not response.is_json

    html = response.get_data(as_text=True)
    assert '500' in html
    assert 'Sistem içi bir hata oluştu' in html or 'hata' in html.lower()
    assert 'Traceback (most recent call last)' not in html
    assert 'RuntimeError: Test amaçlı tetiklenen' not in html

    # 2. API 500 hatası -> JSON response
    with patch('engines.financial_engine.get_live_data', side_effect=RuntimeError("Simulated API failure")):
        res_api_500 = client.get('/api/live-quotes')

    assert res_api_500.status_code == 500
    assert res_api_500.is_json
    json_data = res_api_500.get_json()
    assert json_data.get('success') is False
    assert json_data.get('code') == 500 or json_data.get('error_code') == 'internal_server_error' or 'error' in json_data


@pytest.mark.regression
def test_http_302_and_401_unauthenticated_redirection(client):
    """Giriş yapmamış kullanıcıların korumalı sayfalara eriştiğinde login'e yönlendirildiğini (302) doğrular."""
    protected_paths = [
        '/',
        '/transactions',
        '/assets',
        '/plans',
        '/settings',
        '/analysis',
    ]

    for path in protected_paths:
        response = client.get(path, follow_redirects=False)
        assert response.status_code == 302, f"{path} kimliksiz istekte 302 dönmedi: {response.status_code}"
        assert '/login' in response.headers.get('Location', '')


@pytest.mark.regression
def test_http_403_access_denied_for_unauthorized_user(authenticated_client):
    """Yetkisiz standart kullanıcının admin, monitoring ve depolama alanlarına girmeye çalıştığında erişiminin engellendiğini doğrular."""
    restricted_endpoints = [
        '/admin/',
        '/admin/users',
        '/admin/tenants',
        '/admin/audit',
        '/admin/design_system',
        '/monitoring/',
        '/storage-health/',
    ]
    for endpoint in restricted_endpoints:
        response = authenticated_client.get(endpoint, follow_redirects=False)
        assert response.status_code in [302, 403], f"Yetkisiz erişim açık kaldı ({endpoint}): HTTP {response.status_code}"
        if response.status_code == 302:
            assert endpoint not in response.headers.get('Location', '')


@pytest.mark.regression
def test_http_429_rate_limiting_response(client):
    """429 Too Many Requests yanıtının Retry-After başlığı içerdiğini doğrular (UI ve API)."""
    # UI 429
    with patch('routes.auth.get_daily_insight', side_effect=lambda: abort(429)):
        response = client.get('/login')

    assert response.status_code == 429
    assert not response.is_json
    assert response.headers.get('Retry-After') == '60'

    # API 429
    with patch('engines.financial_engine.get_live_data', side_effect=lambda: abort(429)):
        res_api = client.get('/api/live-quotes')

    assert res_api.status_code == 429
    assert res_api.is_json
    assert res_api.headers.get('Retry-After') == '60'
