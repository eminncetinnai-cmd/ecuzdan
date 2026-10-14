"""HTTP error response contracts used by the local application."""

from flask import abort

from app import app as _test_app


@_test_app.get('/__test__/too-many-requests')
def too_many_requests():
    abort(429)


def test_http_429_response_includes_retry_after_header(authenticated_client):
    response = authenticated_client.get('/__test__/too-many-requests')

    assert response.status_code == 429
    assert response.headers['Retry-After'] == '60'
    assert 'retry' not in response.get_data(as_text=True).lower() or response.headers['Retry-After']


def test_http_404_remains_a_controlled_error_page(client):
    response = client.get('/__test__/missing-resource')

    assert response.status_code == 404
    assert 'Aradığınız sayfa bulunamadı' in response.get_data(as_text=True)


def test_http_404_returns_json_for_api_or_ajax_requests(client):
    # 1. API path
    res_api = client.get('/api/missing-endpoint')
    assert res_api.status_code == 404
    assert res_api.is_json
    data = res_api.get_json()
    assert data.get('success') is False
    assert data.get('code') == 404

    # 2. Accept: application/json header
    res_hdr = client.get('/__test__/missing-resource', headers={'Accept': 'application/json'})
    assert res_hdr.status_code == 404
    assert res_hdr.is_json


def test_http_429_returns_json_for_api_requests(authenticated_client):
    res = authenticated_client.get('/__test__/too-many-requests', headers={'Accept': 'application/json'})
    assert res.status_code == 429
    assert res.is_json
    assert res.headers.get('Retry-After') == '60'
    data = res.get_json()
    assert data.get('success') is False
    assert data.get('code') == 429


def test_unauthenticated_api_request_returns_401_json(client):
    res = client.get('/transactions', headers={'Accept': 'application/json'})
    assert res.status_code == 401
    assert res.is_json
    data = res.get_json()
    assert data.get('success') is False
    assert data.get('error_code') == 'authentication_required'
