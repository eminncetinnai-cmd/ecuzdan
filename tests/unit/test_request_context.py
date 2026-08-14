"""Unit tests for request correlation middleware."""

import pytest

from utils.request_context import REQUEST_ID_HEADER


@pytest.mark.unit
def test_request_context_generates_request_id(client):
    response = client.get('/healthz')

    assert response.status_code == 200
    assert REQUEST_ID_HEADER in response.headers
    assert len(response.headers[REQUEST_ID_HEADER]) > 0


@pytest.mark.unit
def test_request_context_preserves_incoming_header(client):
    response = client.get('/healthz', headers={REQUEST_ID_HEADER: 'incoming-request-id'})

    assert response.headers.get(REQUEST_ID_HEADER) == 'incoming-request-id'
