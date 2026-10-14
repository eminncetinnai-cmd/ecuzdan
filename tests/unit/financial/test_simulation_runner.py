"""
Unit Tests — Simulation Runner (engines/simulation_runner.py)
Mocked HTTP session ile tüm fonksiyonların ve raporlama mantığının testi.
Hedef: %0 → %60+ kapsam artışı
"""
from unittest.mock import MagicMock, mock_open, patch

import pytest
import requests

import engines.simulation_runner as sr


@pytest.fixture(autouse=True)
def reset_test_results():
    """Her test öncesi test_results listesini sıfırla"""
    sr.test_results.clear()
    yield
    sr.test_results.clear()


# ─── log_test ─────────────────────────────────────────────────────────────────

@pytest.mark.unit
def test_log_test_pass():
    sr.log_test("Test 1", "PASS", "Tüm adımlar başarılı")
    assert len(sr.test_results) == 1
    assert sr.test_results[0]["test"] == "Test 1"
    assert sr.test_results[0]["status"] == "PASS"
    assert sr.test_results[0]["details"] == "Tüm adımlar başarılı"


@pytest.mark.unit
def test_log_test_fail():
    sr.log_test("Test Fail", "FAIL", "Hata oluştu")
    assert len(sr.test_results) == 1
    assert sr.test_results[0]["status"] == "FAIL"


# ─── get_csrf_token ───────────────────────────────────────────────────────────

@pytest.mark.unit
def test_get_csrf_token_success():
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.text = '<input type="hidden" name="csrf_token" value="abc-123-xyz">'
    with patch.object(sr.session, 'get', return_value=mock_resp):
        token = sr.get_csrf_token("http://test/login")
        assert token == "abc-123-xyz"


@pytest.mark.unit
def test_get_csrf_token_not_found():
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.text = '<div>No token here</div>'
    with patch.object(sr.session, 'get', return_value=mock_resp):
        token = sr.get_csrf_token("http://test/login")
        assert token is None


@pytest.mark.unit
def test_get_csrf_token_request_exception():
    with patch.object(sr.session, 'get', side_effect=requests.RequestException("Conn error")):
        token = sr.get_csrf_token("http://test/login")
        assert token is None


# ─── test_homepage ────────────────────────────────────────────────────────────

@pytest.mark.unit
def test_homepage_success_200():
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    with patch.object(sr.session, 'get', return_value=mock_resp):
        assert sr.test_homepage() is True
        assert sr.test_results[-1]["status"] == "PASS"


@pytest.mark.unit
def test_homepage_success_302():
    mock_resp = MagicMock()
    mock_resp.status_code = 302
    with patch.object(sr.session, 'get', return_value=mock_resp):
        assert sr.test_homepage() is True
        assert sr.test_results[-1]["status"] == "PASS"


@pytest.mark.unit
def test_homepage_fail_status():
    mock_resp = MagicMock()
    mock_resp.status_code = 500
    with patch.object(sr.session, 'get', return_value=mock_resp):
        assert sr.test_homepage() is False
        assert sr.test_results[-1]["status"] == "FAIL"


@pytest.mark.unit
def test_homepage_exception():
    with patch.object(sr.session, 'get', side_effect=Exception("network down")):
        assert sr.test_homepage() is False
        assert sr.test_results[-1]["status"] == "FAIL"


# ─── test_login_page & test_login ─────────────────────────────────────────────

@pytest.mark.unit
def test_login_page_success():
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    with patch.object(sr.session, 'get', return_value=mock_resp):
        assert sr.test_login_page() is True


@pytest.mark.unit
def test_login_page_fail():
    mock_resp = MagicMock()
    mock_resp.status_code = 404
    with patch.object(sr.session, 'get', return_value=mock_resp):
        assert sr.test_login_page() is False


@pytest.mark.unit
def test_login_success():
    with patch.object(sr, 'get_csrf_token', return_value='csrf-val'):
        mock_resp = MagicMock()
        mock_resp.status_code = 302
        with patch.object(sr.session, 'post', return_value=mock_resp):
            assert sr.test_login() is True
            assert sr.test_results[-1]["status"] == "PASS"


@pytest.mark.unit
def test_login_fail():
    with patch.object(sr, 'get_csrf_token', return_value=None):
        mock_resp = MagicMock()
        mock_resp.status_code = 401
        with patch.object(sr.session, 'post', return_value=mock_resp):
            assert sr.test_login() is False
            assert sr.test_results[-1]["status"] == "FAIL"


# ─── test_dashboard & test_transactions_page ─────────────────────────────────

@pytest.mark.unit
def test_dashboard_success():
    mock_resp = MagicMock(status_code=200)
    with patch.object(sr.session, 'get', return_value=mock_resp):
        assert sr.test_dashboard() is True


@pytest.mark.unit
def test_dashboard_fail():
    mock_resp = MagicMock(status_code=403)
    with patch.object(sr.session, 'get', return_value=mock_resp):
        assert sr.test_dashboard() is False


@pytest.mark.unit
def test_transactions_page_success():
    mock_resp = MagicMock(status_code=200)
    with patch.object(sr.session, 'get', return_value=mock_resp):
        assert sr.test_transactions_page() is True


@pytest.mark.unit
def test_transactions_page_fail():
    mock_resp = MagicMock(status_code=500)
    with patch.object(sr.session, 'get', return_value=mock_resp):
        assert sr.test_transactions_page() is False


# ─── test_add_transaction ─────────────────────────────────────────────────────

@pytest.mark.unit
def test_add_transaction_success():
    with patch.object(sr, 'get_csrf_token', return_value='token-123'):
        mock_resp = MagicMock(status_code=302)
        with patch.object(sr.session, 'post', return_value=mock_resp):
            assert sr.test_add_transaction() is True
            assert sr.test_results[-1]["status"] == "PASS"


@pytest.mark.unit
def test_add_transaction_fail():
    with patch.object(sr, 'get_csrf_token', return_value=None):
        mock_resp = MagicMock(status_code=400)
        with patch.object(sr.session, 'post', return_value=mock_resp):
            assert sr.test_add_transaction() is False


# ─── test_categories_page & test_add_category ─────────────────────────────────

@pytest.mark.unit
def test_categories_page_success():
    mock_resp = MagicMock(status_code=200)
    with patch.object(sr.session, 'get', return_value=mock_resp):
        assert sr.test_categories_page() is True


@pytest.mark.unit
def test_add_category_success():
    with patch.object(sr, 'get_csrf_token', return_value='token-cat'):
        mock_resp = MagicMock(status_code=200)
        with patch.object(sr.session, 'post', return_value=mock_resp):
            assert sr.test_add_category() is True


@pytest.mark.unit
def test_add_category_fail():
    with patch.object(sr, 'get_csrf_token', return_value='token-cat'):
        mock_resp = MagicMock(status_code=500)
        with patch.object(sr.session, 'post', return_value=mock_resp):
            assert sr.test_add_category() is False


# ─── test_assets_page & test_add_asset ─────────────────────────────────────────

@pytest.mark.unit
def test_assets_page_success():
    mock_resp = MagicMock(status_code=200)
    with patch.object(sr.session, 'get', return_value=mock_resp):
        assert sr.test_assets_page() is True


@pytest.mark.unit
def test_add_asset_success():
    with patch.object(sr, 'get_csrf_token', return_value='token-asset'):
        mock_resp = MagicMock(status_code=302)
        with patch.object(sr.session, 'post', return_value=mock_resp):
            assert sr.test_add_asset() is True


@pytest.mark.unit
def test_add_asset_fail():
    with patch.object(sr, 'get_csrf_token', return_value=None):
        mock_resp = MagicMock(status_code=422)
        with patch.object(sr.session, 'post', return_value=mock_resp):
            assert sr.test_add_asset() is False


# ─── test_plans_page, test_settings_page, test_language_switching, test_logout

@pytest.mark.unit
def test_plans_page_success():
    mock_resp = MagicMock(status_code=200)
    with patch.object(sr.session, 'get', return_value=mock_resp):
        assert sr.test_plans_page() is True


@pytest.mark.unit
def test_settings_page_success():
    mock_resp = MagicMock(status_code=200)
    with patch.object(sr.session, 'get', return_value=mock_resp):
        assert sr.test_settings_page() is True


@pytest.mark.unit
def test_language_switching_success():
    mock_resp = MagicMock(status_code=200)
    with patch.object(sr.session, 'get', return_value=mock_resp):
        assert sr.test_language_switching() is True


@pytest.mark.unit
def test_language_switching_fail():
    mock_resp_tr = MagicMock(status_code=200)
    mock_resp_en = MagicMock(status_code=500)
    with patch.object(sr.session, 'get', side_effect=[mock_resp_tr, mock_resp_en]):
        assert sr.test_language_switching() is False


@pytest.mark.unit
def test_logout_success():
    mock_resp = MagicMock(status_code=302)
    with patch.object(sr.session, 'get', return_value=mock_resp):
        assert sr.test_logout() is True


@pytest.mark.unit
def test_logout_fail():
    mock_resp = MagicMock(status_code=500)
    with patch.object(sr.session, 'get', return_value=mock_resp):
        assert sr.test_logout() is False


# ─── generate_report & main ───────────────────────────────────────────────────

@pytest.mark.unit
def test_generate_report():
    sr.log_test("T1", "PASS", "ok")
    sr.log_test("T2", "FAIL", "bad")
    m_open = mock_open()
    with patch("builtins.open", m_open):
        sr.generate_report()
        m_open.assert_called_once_with("test_report.json", "w", encoding="utf-8")


@pytest.mark.unit
def test_main():
    with patch.object(sr, 'test_homepage', return_value=True), \
         patch.object(sr, 'test_login_page', return_value=True), \
         patch.object(sr, 'test_login', return_value=True), \
         patch.object(sr, 'test_dashboard', return_value=True), \
         patch.object(sr, 'test_transactions_page', return_value=True), \
         patch.object(sr, 'test_add_transaction', return_value=True), \
         patch.object(sr, 'test_categories_page', return_value=True), \
         patch.object(sr, 'test_add_category', return_value=True), \
         patch.object(sr, 'test_assets_page', return_value=True), \
         patch.object(sr, 'test_add_asset', return_value=True), \
         patch.object(sr, 'test_plans_page', return_value=True), \
         patch.object(sr, 'test_settings_page', return_value=True), \
         patch.object(sr, 'test_language_switching', return_value=True), \
         patch.object(sr, 'test_logout', return_value=True), \
         patch.object(sr, 'generate_report') as mock_report:
        sr.main()
        mock_report.assert_called_once()
