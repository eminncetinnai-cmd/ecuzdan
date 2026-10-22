"""Unit tests for IBAN endpoints in logbook routes."""

from unittest.mock import Mock, patch
import pytest


@pytest.mark.unit
def test_logbook_index_with_iban_tab(authenticated_client):
    with patch('routes.logbook._get_iban_service') as mock_iban_svc_getter:
        mock_iban_svc = Mock()
        mock_iban_svc.list_ibans.return_value = []
        mock_iban_svc_getter.return_value = mock_iban_svc

        response = authenticated_client.get('/logbook/?tab=ibans')
        assert response.status_code == 200
        html = response.get_data(as_text=True)
        assert "IBAN & Hesap Rehberi" in html
        assert "Kayıtlı IBAN Numaralarım" in html


@pytest.mark.unit
def test_create_iban_ajax_success(authenticated_client):
    with patch('routes.logbook._get_iban_service') as mock_iban_svc_getter:
        mock_iban_svc = Mock()
        mock_record = Mock()
        mock_record.to_dict.return_value = {
            'id': 1,
            'title': 'Garanti Maaş',
            'iban': 'TR330006200511123456789012',
            'bank_name': 'Garanti BBVA',
        }
        mock_iban_svc.create_iban.return_value = mock_record
        mock_iban_svc_getter.return_value = mock_iban_svc

        response = authenticated_client.post(
            '/logbook/ibans/create',
            data={
                'title': 'Garanti Maaş',
                'iban': 'TR33 0006 2005 1112 3456 7890 12',
                'bank_name': 'Garanti BBVA',
                'category': 'kendi_hesabim',
            },
            headers={'X-Requested-With': 'XMLHttpRequest'},
        )
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert data['iban']['bank_name'] == 'Garanti BBVA'


@pytest.mark.unit
def test_create_iban_validation_failure(authenticated_client):
    response = authenticated_client.post(
        '/logbook/ibans/create',
        data={'title': '', 'iban': ''},
        headers={'X-Requested-With': 'XMLHttpRequest'},
    )
    assert response.status_code == 400
    data = response.get_json()
    assert data['success'] is False
    assert "zorunludur" in data['message']


@pytest.mark.unit
def test_detail_iban(authenticated_client):
    with patch('routes.logbook._get_iban_service') as mock_iban_svc_getter:
        mock_iban_svc = Mock()
        mock_record = Mock()
        mock_record.to_dict.return_value = {
            'id': 5,
            'title': 'Ev Sahibi Kira',
            'iban': 'TR120006400511123456789012',
            'bank_name': 'İş Bankası',
        }
        mock_iban_svc.get_iban.return_value = mock_record
        mock_iban_svc_getter.return_value = mock_iban_svc

        response = authenticated_client.get(
            '/logbook/ibans/5',
            headers={'X-Requested-With': 'XMLHttpRequest'},
        )
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert data['iban']['id'] == 5


@pytest.mark.unit
def test_delete_iban(authenticated_client):
    with patch('routes.logbook._get_iban_service') as mock_iban_svc_getter:
        mock_iban_svc = Mock()
        mock_iban_svc.delete_iban.return_value = True
        mock_iban_svc_getter.return_value = mock_iban_svc

        response = authenticated_client.post(
            '/logbook/ibans/5/delete',
            headers={'X-Requested-With': 'XMLHttpRequest'},
        )
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True


@pytest.mark.unit
def test_api_detect_bank(authenticated_client):
    response = authenticated_client.get('/logbook/api/ibans/detect-bank?iban=TR330006200511123456789012')
    assert response.status_code == 200
    data = response.get_json()
    assert data['success'] is True
    assert data['bank_name'] == 'Garanti BBVA'
    assert data['formatted_iban'] == 'TR33 0006 2005 1112 3456 7890 12'
    assert data['is_valid'] is True


@pytest.mark.unit
def test_toggle_favorite_iban_ajax(authenticated_client):
    with patch('routes.logbook._get_iban_service') as mock_iban_svc_getter:
        mock_iban_svc = Mock()
        mock_record = Mock()
        mock_record.is_favorite = True
        mock_record.to_dict.return_value = {'id': 5, 'is_favorite': True}
        mock_iban_svc.toggle_favorite.return_value = mock_record
        mock_iban_svc_getter.return_value = mock_iban_svc

        response = authenticated_client.post(
            '/logbook/ibans/5/toggle-favorite',
            headers={'X-Requested-With': 'XMLHttpRequest'},
        )
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert data['is_favorite'] is True
        assert "favorilere eklendi" in data['message']


@pytest.mark.unit
def test_toggle_favorite_iban_not_found(authenticated_client):
    with patch('routes.logbook._get_iban_service') as mock_iban_svc_getter:
        mock_iban_svc = Mock()
        mock_iban_svc.toggle_favorite.return_value = None
        mock_iban_svc_getter.return_value = mock_iban_svc

        response = authenticated_client.post(
            '/logbook/ibans/999/toggle-favorite',
            headers={'X-Requested-With': 'XMLHttpRequest'},
        )
        assert response.status_code == 400
        data = response.get_json()
        assert data['success'] is False
        assert "bulunamadı" in data['message']


@pytest.mark.unit
def test_update_iban_ajax_success(authenticated_client):
    with patch('routes.logbook._get_iban_service') as mock_iban_svc_getter:
        mock_iban_svc = Mock()
        mock_record = Mock()
        mock_record.to_dict.return_value = {
            'id': 1,
            'title': 'Güncel Başlık',
            'iban': 'TR330006200511123456789012',
            'is_favorite': True,
        }
        mock_iban_svc.update_iban.return_value = mock_record
        mock_iban_svc_getter.return_value = mock_iban_svc

        response = authenticated_client.post(
            '/logbook/ibans/1/update',
            data={
                'title': 'Güncel Başlık',
                'iban': 'TR330006200511123456789012',
                'is_favorite': '1',
                'category': 'kendi_hesabim',
            },
            headers={'X-Requested-With': 'XMLHttpRequest'},
        )
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert data['iban']['title'] == 'Güncel Başlık'
