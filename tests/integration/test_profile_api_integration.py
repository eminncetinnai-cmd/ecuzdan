"""Integration tests for the investor profile API endpoints."""

import json

import pytest


@pytest.mark.integration
class TestProfileAPIIntegration:
    """Validate the public contract of the profile API routes."""

    def test_api_questions_endpoint_structure(self, client):
        response = client.get('/profile/api/questions')

        assert response.status_code in {200, 302, 401}
        if response.status_code == 200:
            data = json.loads(response.data)
            assert data.get('success') is True
            assert isinstance(data.get('questions'), list)
            if data['questions']:
                question = data['questions'][0]
                assert {'id', 'dimension', 'type', 'question', 'options'} <= set(question)

    def test_api_submit_endpoint_missing_answers(self, client):
        response = client.post('/profile/api/submit', json={'answers': []})

        assert response.status_code in {302, 400, 401, 422}

    def test_api_submit_endpoint_invalid_format(self, client):
        response = client.post('/profile/api/submit', json={'invalid': 'data'})

        assert response.status_code in {302, 400, 401, 422}

    def test_api_profile_endpoint(self, client):
        response = client.get('/profile/api/profile/1')

        assert response.status_code in {200, 302, 401, 404}

    def test_api_history_endpoint(self, client):
        response = client.get('/profile/api/history')

        assert response.status_code in {200, 302, 401}

    def test_profile_index_page(self, client):
        response = client.get('/profile')

        assert response.status_code in {200, 302, 308}

    def test_profile_start_page(self, client):
        response = client.get('/profile/start')

        assert response.status_code in {200, 302, 308}

    def test_profile_result_page(self, client):
        response = client.get('/profile/result/1')

        assert response.status_code in {200, 302, 404}



